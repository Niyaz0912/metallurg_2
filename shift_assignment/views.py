import logging
from datetime import timezone, datetime
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, FormView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from production_plan.forms import ExcelUploadForm
from .models import ShiftAssignment, ShiftAssignmentArchive
from production_plan.models import ProductionPlan
from .forms import ShiftAssignmentForm
from django.contrib.auth import get_user_model

from django.http import HttpResponse
import pandas as pd
from io import BytesIO
logger = logging.getLogger(__name__)
User = get_user_model()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = ['master', 'director']

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас нет прав для просмотра этой страницы")
        return super().handle_no_permission()


class ShiftAssignmentListView(LoginRequiredMixin, ListView):
    model = ShiftAssignment
    template_name = 'shift_assignment/list.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        user = self.request.user

        if user.role == 'operator':
            return ShiftAssignment.objects.filter(
                operator=user,
                status__in=[ShiftAssignment.Status.PLANNED, ShiftAssignment.Status.IN_PROGRESS]
            ).order_by('-shift_date')
        else:
            return ShiftAssignment.objects.filter(
                status__in=[ShiftAssignment.Status.PLANNED, ShiftAssignment.Status.IN_PROGRESS]
            ).order_by('-shift_date')


class ShiftAssignmentCreateView(StaffRequiredMixin, CreateView):
    model = ShiftAssignment
    form_class = ShiftAssignmentForm
    template_name = 'shift_assignment/create.html'
    success_url = reverse_lazy('shift_assignment:list')

    def form_valid(self, form):
        # Если в модели нет поля created_by, эту строку можно убрать
        # form.instance.created_by = self.request.user
        messages.success(self.request, "Задание успешно создано")
        return super().form_valid(form)


class ShiftAssignmentUpdateView(StaffRequiredMixin, UpdateView):
    model = ShiftAssignment
    form_class = ShiftAssignmentForm
    template_name = 'shift_assignment/update.html'
    success_url = reverse_lazy('shift_assignment:list')

    def form_valid(self, form):
        # Используем константы для статусов
        if form.instance.status == ShiftAssignment.Status.COMPLETED and not form.instance.completed_at:
            form.instance.completed_at = timezone.now()
            # Создаём архивное задание
            ShiftAssignmentArchive.create_from_assignment(form.instance)
        messages.success(self.request, "Задание успешно обновлено")
        return super().form_valid(form)


class ShiftAssignmentDeleteView(StaffRequiredMixin, DeleteView):
    model = ShiftAssignment
    template_name = 'shift_assignment/delete.html'
    success_url = reverse_lazy('shift_assignment:list')


class ShiftAssignmentDetailView(LoginRequiredMixin, DetailView):
    model = ShiftAssignment
    template_name = 'shift_assignment/detail.html'
    context_object_name = 'assignment'


class CompleteAssignmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        actual_quantity = request.POST.get('actual_quantity')

        try:
            actual_quantity = int(actual_quantity)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Некорректное количество'})

        success, message = assignment.complete_assignment(actual_quantity, request.user)
        return JsonResponse({'success': success, 'message': message})


class ShiftAssignmentArchiveView(LoginRequiredMixin, ListView):
    model = ShiftAssignmentArchive
    template_name = 'shift_assignment/archive.html'
    context_object_name = 'archived_assignments'

    def get_queryset(self):
        return ShiftAssignmentArchive.objects.all().order_by('-archived_at')


class ShiftAssignmentUploadView(LoginRequiredMixin, FormView):
    template_name = 'shift_assignment/upload.html'
    form_class = ExcelUploadForm
    success_url = reverse_lazy('shift_assignment:list')

    column_mapping = {
        'Наименование заказа': 'order_name',
        'Заказчик': 'customer',
        'Дата смены': 'shift_date',
        'Тип смены': 'shift_type',
        'Логин оператора': 'operator_username',
        'Плановое количество': 'planned_quantity',
        'Номер станка': 'machine_number',
        'Примечания': 'notes'
    }

    required_columns = [
        'Наименование заказа',
        'Заказчик',
        'Дата смены',
        'Тип смены',
        'Логин оператора',
        'Плановое количество'
    ]

    def form_valid(self, form):
        excel_file = form.cleaned_data['excel_file']
        try:
            df = pd.read_excel(excel_file)

            missing = set(self.required_columns) - set(df.columns)
            if missing:
                messages.error(self.request, f"Отсутствуют обязательные колонки: {', '.join(missing)}")
                return self.form_invalid(form)

            df.rename(columns=self.column_mapping, inplace=True)

            created_count = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    operator = User.objects.get(username=row['operator_username'], role='operator')
                    shift_date = datetime.strptime(str(row['shift_date']), '%d.%m.%Y').date()
                    plan = ProductionPlan.objects.get(order_name=row['order_name'], customer=row['customer'])

                    ShiftAssignment.objects.create(
                        production_plan=plan,
                        shift_date=shift_date,
                        shift_type=row['shift_type'],
                        operator=operator,
                        planned_quantity=row['planned_quantity'],
                        machine_number=row.get('machine_number', ''),
                        notes=row.get('notes', '')
                    )
                    created_count += 1

                except User.DoesNotExist:
                    error_details.append(f"Строка {index + 2}: Оператор '{row.get('operator_username', '?')}' не найден")
                except ProductionPlan.DoesNotExist:
                    error_details.append(f"Строка {index + 2}: Производственный план не найден (Заказ: {row.get('order_name', '?')}, Заказчик: {row.get('customer', '?')})")
                except Exception as e:
                    error_details.append(f"Строка {index + 2}: {str(e)}")

            if created_count:
                messages.success(self.request, f"Успешно создано {created_count} сменных заданий.")

            if error_details:
                messages.warning(self.request, f"Не удалось создать {len(error_details)} заданий:")
                for err in error_details[:3]:
                    messages.error(self.request, err)
                if len(error_details) > 3:
                    messages.info(self.request, f"...и ещё {len(error_details) - 3} ошибок")

        except Exception as e:
            messages.error(self.request, f"Ошибка при обработке файла: {str(e)}")
            logger.error(f"Ошибка загрузки файла: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)


@login_required
def complete_assignment(request, pk):
    if request.method == 'POST':
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        actual_quantity = request.POST.get('actual_quantity')

        try:
            actual_quantity = int(actual_quantity)
        except (TypeError, ValueError):
            messages.error(request, "Некорректное количество")
            return redirect('shift_assignment:detail', pk=pk)

        success, message = assignment.complete_assignment(actual_quantity, request.user)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('shift_assignment:detail', pk=pk)
    else:
        return redirect('shift_assignment:detail', pk=pk)


def download_rus_template(request):
    df = pd.DataFrame(columns=[
        'Заказчик',
        'Наименование заказа',
        'Дата смены',
        'Тип смены',
        'Логин оператора',
        'Плановое количество',
        'Номер станка',
        'Примечания'
    ])

    df.loc[0] = [
        'ООО "МеталлСтрой"',
        'MS-2023-001',
        '15.05.2025',
        'day',
        'Khasanov.N',
        100,
        'CNC-01',
        'Пример примечания'
    ]

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Шаблон')
    writer.close()
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=шаблон_сменных_заданий.xlsx'
    return response
