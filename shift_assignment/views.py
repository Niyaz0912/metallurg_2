import logging
from datetime import datetime
from io import BytesIO
import pandas as pd
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone

from production_plan.models import ProductionPlan
from .forms import ShiftAssignmentForm, UpdateShiftAssignmentForm, ExcelUploadForm, EditShiftAssignmentForm
from .models import ShiftAssignment

logger = logging.getLogger(__name__)
User = get_user_model()


class ActiveAssignmentsView(LoginRequiredMixin, ListView):
    """Список активных заданий"""
    model = ShiftAssignment
    template_name = 'shift_assignment/active_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        queryset = ShiftAssignment.objects.filter(
            status=ShiftAssignment.Status.ASSIGNMENT
        ).select_related('operator', 'production_plan')

        # Фильтрация по оператору (если запрос от оператора)
        if self.request.user.role == 'operator':
            queryset = queryset.filter(operator=self.request.user)

        return queryset.order_by('-shift_date', 'shift_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Активные задания"
        return context


class CompletedAssignmentsView(LoginRequiredMixin, ListView):
    """Список выполненных заданий"""
    model = ShiftAssignment
    template_name = 'shift_assignment/completed_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        queryset = ShiftAssignment.objects.filter(
            status=ShiftAssignment.Status.COMPLETED
        ).select_related('operator', 'production_plan')

        # Фильтрация по оператору (если запрос от оператора)
        if self.request.user.role == 'operator':
            queryset = queryset.filter(operator=self.request.user)

        return queryset.order_by('-completed_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Выполненные задания"
        return context


class ShiftAssignmentCreateView(LoginRequiredMixin, CreateView):
    """Создание нового задания"""
    model = ShiftAssignment
    form_class = ShiftAssignmentForm
    template_name = 'shift_assignment/create.html'
    success_url = reverse_lazy('shift_assignment:active')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Задание успешно создано")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Создание нового задания"
        return context


class ShiftAssignmentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование задания"""
    model = ShiftAssignment
    form_class = EditShiftAssignmentForm
    template_name = 'shift_assignment/update.html'

    def get_success_url(self):
        return reverse_lazy('shift_assignment:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Редактирование задания"
        return context


class ShiftAssignmentDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о задании"""
    model = ShiftAssignment
    template_name = 'shift_assignment/detail.html'
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Задание #{self.object.id}"

        # Добавляем форму завершения задания если оно активно и пользователь оператор
        if (self.object.status == ShiftAssignment.Status.ASSIGNMENT and
                (self.request.user == self.object.operator or self.request.user.is_superuser)):
            context['complete_form'] = UpdateShiftAssignmentForm(instance=self.object)

        return context


class ShiftAssignmentDeleteView(LoginRequiredMixin, DeleteView):
    model = ShiftAssignment
    template_name = 'shift_assignment/delete.html'

    def get_success_url(self):
        # Редирект на профиль авторизованного пользователя
        return reverse_lazy('users:profile', kwargs={'username': self.request.user.username})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Задание успешно удалено")
        return super().delete(request, *args, **kwargs)


@login_required
def delete_all_assignments(request):
    if request.method == 'POST':
        try:
            active_assignments = ShiftAssignment.objects.filter(status=ShiftAssignment.Status.ASSIGNMENT)
            count = active_assignments.count()
            active_assignments.delete()

            messages.success(request, f'Успешно удалено {count} активных заданий')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении заданий: {str(e)}')

    # Редирект на профиль авторизованного пользователя
    return redirect('users:profile', username=request.user.username)


class CompleteAssignmentView(LoginRequiredMixin, View):
    """Завершение задания"""

    def post(self, request, pk):
        assignment = get_object_or_404(ShiftAssignment, pk=pk)

        # Проверяем права пользователя
        if not (request.user == assignment.operator or request.user.is_superuser or request.user.role == 'master'):
            messages.error(request, "У вас нет прав для завершения этого задания")
            return redirect('shift_assignment:detail', pk=pk)

        # Получаем фактическое количество из формы
        actual_quantity = request.POST.get('actual_quantity')

        try:
            actual_quantity = int(actual_quantity)
        except (TypeError, ValueError):
            messages.error(request, "Укажите корректное количество")
            return redirect('shift_assignment:detail', pk=pk)

        # Вызываем метод complete модели
        success, message = assignment.complete(actual_quantity, request.user)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('shift_assignment:detail', pk=pk)


class ShiftAssignmentUploadView(LoginRequiredMixin, View):
    """Загрузка заданий из Excel с поддержкой общих данных"""
    template_name = 'shift_assignment/upload.html'
    success_url = '/users/profile/master/'

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
    required_columns = ['Наименование заказа', 'Заказчик', 'Логин оператора', 'Плановое количество']

    SHIFT_TYPE_MAP = {
        'день': 'day',
        'ночь': 'night',
        'day': 'day',
        'night': 'night',
    }

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

            # Проверка обязательных колонок
            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                messages.error(request, f"Отсутствуют обязательные колонки: {', '.join(missing_cols)}")
                return render(request, self.template_name, {'form': form})

            # Автозаполнение даты и типа смены, если они указаны в первой строке
            common_shift_date = None
            common_shift_type = None

            if 'Дата смены' in df.columns:
                common_shift_date = self.parse_date(df['Дата смены'].iloc[0]) if not pd.isna(
                    df['Дата смены'].iloc[0]) else None
                df['shift_date'] = common_shift_date

            if 'Тип смены' in df.columns:
                raw_shift_type = str(df['Тип смены'].iloc[0]).strip().lower() if not pd.isna(
                    df['Тип смены'].iloc[0]) else None
                common_shift_type = self.SHIFT_TYPE_MAP.get(raw_shift_type)
                df['shift_type'] = common_shift_type

            # Проверка что общие данные заполнены
            if not common_shift_date:
                messages.error(request, "Дата смены должна быть указана в первой строке")
                return render(request, self.template_name, {'form': form})

            if not common_shift_type:
                messages.error(request, "Тип смены должен быть 'день' или 'ночь' (или 'day'/'night')")
                return render(request, self.template_name, {'form': form})

            df = df.rename(columns=self.column_mapping)
            created_count = 0
            errors = []

            for idx, row in df.iterrows():
                row_num = idx + 2
                try:
                    # Пропускаем первую строку если она содержит только общие данные
                    if idx == 0 and pd.isna(row.get('operator_username')):
                        continue

                    plan = ProductionPlan.objects.get(
                        order_name=row['order_name'],
                        customer=row['customer']
                    )
                    operator = User.objects.get(username=row['operator_username'])

                    ShiftAssignment.objects.create(
                        production_plan=plan,
                        shift_date=common_shift_date,  # Используем общую дату
                        shift_type=common_shift_type,  # Используем общий тип смены
                        machine_number=row.get('machine_number', ''),
                        operator=operator,
                        planned_quantity=row['planned_quantity'],
                        notes=row.get('notes', ''),
                        status=ShiftAssignment.Status.ASSIGNMENT
                    )
                    created_count += 1
                except ProductionPlan.DoesNotExist:
                    errors.append(f"Строка {row_num}: План производства не найден")
                except User.DoesNotExist:
                    errors.append(f"Строка {row_num}: Оператор не найден")
                except ValueError as ve:
                    errors.append(f"Строка {row_num}: {str(ve)}")
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
            logger.exception("Ошибка при загрузке файла с заданиями")
            return render(request, self.template_name, {'form': form})

    def parse_date(self, date_value):
        """Парсинг даты из разных форматов"""
        if pd.isna(date_value):
            raise ValueError("Дата не может быть пустой")
        if isinstance(date_value, datetime):
            return date_value.date()
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(str(date_value), fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Неподдерживаемый формат даты: {date_value}")


def download_rus_template(request):
    """Скачивание шаблона Excel"""
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
        'operator1',
        100,
        'CNC-01',
        'Пример примечания'
    ]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Шаблон')

    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=шаблон_сменных_заданий.xlsx'
    return response
