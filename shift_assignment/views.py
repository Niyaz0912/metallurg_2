import logging
from datetime import timezone, datetime
from io import BytesIO

import pandas as pd

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from production_plan.models import ProductionPlan
from production_plan.forms import ExcelUploadForm
from production_plan.views import StaffRequiredMixin
from .forms import ShiftAssignmentForm
from .models import ShiftAssignment, ShiftAssignmentArchive
from django.contrib.auth.decorators import login_required


logger = logging.getLogger(__name__)
User = get_user_model()


class ShiftAssignmentListView(LoginRequiredMixin, ListView):
    model = ShiftAssignment
    template_name = 'shift_assignment/list.html'
    context_object_name = 'shift_assignments'

    def get_queryset(self):
        # Фильтруем по статусу "Задание на смену"
        return ShiftAssignment.objects.filter(status=ShiftAssignment.Status.ASSIGNMENT).order_by('-shift_date')


class ShiftAssignmentUploadView(LoginRequiredMixin, View):
    template_name = 'shift_assignment/upload.html'
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

    required_columns = list(column_mapping.keys())

    def get(self, request):
        form = ExcelUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ExcelUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        excel_file = request.FILES['excel_file']

        try:
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()

            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                messages.error(request, f"Отсутствуют колонки: {', '.join(missing_cols)}")
                return render(request, self.template_name, {'form': form})

            df = df.rename(columns=self.column_mapping)

            created_count = 0
            errors = []

            for idx, row in df.iterrows():
                row_num = idx + 2
                try:
                    shift_date = self.parse_date(row['shift_date'])

                    plan = ProductionPlan.objects.get(order_name=row['order_name'], customer=row['customer'])
                    operator = User.objects.get(username=row['operator_username'])

                    ShiftAssignment.objects.create(
                        production_plan=plan,
                        shift_date=shift_date,
                        shift_type=row['shift_type'],
                        machine_number=row.get('machine_number', ''),
                        operator=operator,
                        planned_quantity=row['planned_quantity'],
                        notes=row.get('notes', ''),
                        status=ShiftAssignment.Status.ASSIGNMENT  # Устанавливаем статус "Задание на смену"
                    )
                    created_count += 1

                except ProductionPlan.DoesNotExist:
                    errors.append(f"Строка {row_num}: План производства не найден (Заказ: {row.get('order_name')}, Заказчик: {row.get('customer')})")
                except User.DoesNotExist:
                    errors.append(f"Строка {row_num}: Оператор с логином '{row.get('operator_username')}' не найден")
                except ValueError as ve:
                    errors.append(f"Строка {row_num}: Ошибка с датой: {ve}")
                except Exception as e:
                    errors.append(f"Строка {row_num}: Ошибка: {str(e)}")
                    logger.error(f"Ошибка в строке {row_num}: {str(e)}")

            if created_count > 0:
                messages.success(request, f"Успешно создано заданий: {created_count}")

            if errors:
                messages.warning(request, f"Ошибки в {len(errors)} строках:")
                for err in errors[:5]:
                    messages.error(request, err)
                if len(errors) > 5:
                    messages.info(request, f"И ещё {len(errors) - 5} ошибок...")

            return redirect(self.success_url)

        except Exception as e:
            messages.error(request, f"Ошибка при обработке файла: {str(e)}")
            logger.exception("Ошибка при загрузке сменных заданий")
            return render(request, self.template_name, {'form': form})

    def parse_date(self, date_value):
        if pd.isna(date_value):
            raise ValueError("Дата не может быть пустой")
        if isinstance(date_value, datetime):
            return date_value.date()
        for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(date_value), fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Неподдерживаемый формат даты: {date_value}")


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
