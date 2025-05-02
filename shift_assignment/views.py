import logging

import pandas as pd
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required  # Добавлен импорт
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils import timezone  # Добавлен импорт
from .models import ShiftAssignment, ShiftAssignmentArchive
from .forms import ShiftAssignmentForm, UpdateShiftAssignmentForm
from django.views.generic import View
from django.contrib import messages

logger = logging.getLogger(__name__)
User = get_user_model()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки ролей master и director"""

    def test_func(self):
        return self.request.user.role in ['master', 'director']

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас нет прав для этого действия")
        return super().handle_no_permission()


class ShiftAssignmentListView(LoginRequiredMixin, ListView):
    model = ShiftAssignment
    template_name = 'shift_assignment/list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        if user.role == 'operator':
            # Для оператора - только его задания
            return ShiftAssignment.objects.filter(
                operator_id=user.username,
                execution_status=False
            ).order_by('-date')

        # Для мастеров/директоров - все активные задания
        return ShiftAssignment.objects.filter(
            execution_status=False
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Активные сменные задания'
        context['can_edit'] = self.request.user.role in ['master', 'director']
        return context


class ShiftAssignmentCreateView(StaffRequiredMixin, CreateView):
    model = ShiftAssignment
    form_class = ShiftAssignmentForm
    template_name = 'shift_assignment/create.html'
    success_url = reverse_lazy('shift_assignment:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Сменное задание успешно создано')
        return super().form_valid(form)


class ShiftAssignmentUpdateView(StaffRequiredMixin, UpdateView):
    model = ShiftAssignment
    form_class = UpdateShiftAssignmentForm
    template_name = 'shift_assignment/update.html'

    def form_valid(self, form):
        if form.instance.execution_status and not form.instance.completed_at:
            form.instance.completed_at = timezone.now()
            ShiftAssignmentArchive.objects.create_from_assignment(form.instance)
            messages.success(self.request, 'Задание выполнено и перемещено в архив')
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.execution_status:
            return reverse_lazy('shift_assignment:archive')
        return reverse_lazy('shift_assignment:list')


class ShiftAssignmentDeleteView(StaffRequiredMixin, DeleteView):
    model = ShiftAssignment
    template_name = 'shift_assignment/delete.html'
    success_url = reverse_lazy('shift_assignment:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Задание успешно удалено')
        return super().delete(request, *args, **kwargs)


class ShiftAssignmentDetailView(LoginRequiredMixin, DetailView):
    model = ShiftAssignment
    template_name = 'shift_assignment/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.role in ['master', 'director']
        return context


class CompleteAssignmentView(LoginRequiredMixin, View):
    """Обработка отметки о выполнении задания оператором"""

    def post(self, request, pk):
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        success, message = assignment.complete(request.user)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('users:profile', username=request.user.username)


class ShiftAssignmentArchiveView(LoginRequiredMixin, ListView):
    model = ShiftAssignmentArchive
    template_name = 'shift_assignment/archive.html'
    context_object_name = 'archived_shifts'
    paginate_by = 20

    def get_queryset(self):
        return ShiftAssignmentArchive.objects.all().order_by('-completed_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Архив выполненных смен'
        return context


@login_required
def upload_shift_assignments(request):
    if request.user.role not in ['master', 'director']:
        raise PermissionDenied("Только мастер или директор могут загружать задания")

    template_name = 'shift_assignment/upload.html'
    context = {
        'title': 'Загрузка сменных заданий из Excel',
        'example_columns': [
            'customer (обязательно)',
            'date (обязательно, формат ДД.ММ.ГГГГ)',
            'machine_number (обязательно, число)',
            'operator/operator_id (обязательно, логин пользователя)',
            'order (обязательно)',
            'part (обязательно)',
            'quantity (обязательно, число)',
            'comment (необязательно)'
        ],
        'example_file_url': '/static/files/shift_assignment_example.xlsx'
    }

    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Файл не выбран')
            return render(request, template_name, context)

        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Поддерживаются только файлы Excel (.xlsx, .xls)')
            return render(request, template_name, context)

        try:
            # Чтение файла
            df = pd.read_excel(file)

            # Определение названия колонки с оператором
            operator_col = None
            for col in ['operator', 'operator_id']:
                if col in df.columns:
                    operator_col = col
                    break

            # Проверка обязательных колонок
            required_columns = [
                'customer',
                'date',
                'machine_number',
                operator_col,
                'order',
                'part',
                'quantity'
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(
                    request,
                    f'Отсутствуют обязательные колонки: {", ".join(missing_columns)}'
                )
                return render(request, template_name, context)

            success_count = 0
            errors = []
            duplicates = 0

            for idx, row in df.iterrows():
                try:
                    # Валидация данных
                    if pd.isna(row['customer']) or not str(row['customer']).strip():
                        raise ValueError("Не указан клиент")

                    if pd.isna(row[operator_col]):
                        raise ValueError("Не указан оператор")

                    operator = User.objects.get(username=row[operator_col])

                    # Проверка дубликатов
                    if ShiftAssignment.objects.filter(
                            date=row['date'],
                            machine_number=row['machine_number'],
                            operator=operator,
                            order=row['order']
                    ).exists():
                        duplicates += 1
                        continue

                    # Создание задания
                    ShiftAssignment.objects.create(
                        customer=row['customer'],
                        date=row['date'],
                        machine_number=int(row['machine_number']),
                        operator=operator,
                        order=row['order'],
                        part=row['part'],
                        quantity=int(row['quantity']),
                        comment=row.get('comment', ''),
                        production_plan_id=row.get('production_plan_id')
                    )
                    success_count += 1

                except User.DoesNotExist:
                    errors.append(f'Строка {idx + 2}: Оператор "{row[operator_col]}" не найден')
                except ValueError as e:
                    errors.append(f'Строка {idx + 2}: {str(e)}')
                except Exception as e:
                    errors.append(f'Строка {idx + 2}: Ошибка - {str(e)}')

            # Формирование итоговых сообщений
            if success_count > 0:
                messages.success(
                    request,
                    f'Успешно загружено {success_count} заданий'
                )

            if duplicates > 0:
                messages.warning(
                    request,
                    f'Пропущено {duplicates} дубликатов (задания уже существуют)'
                )

            if errors:
                error_msg = f'Найдено {len(errors)} ошибок. Первые 5:'
                messages.error(request, error_msg)
                for error in errors[:5]:
                    messages.error(request, error)

                # Запись всех ошибок в лог
                logger.error(f"Ошибки при загрузке файла {file.name}: {errors}")

            return redirect('shift_assignment:list')

        except Exception as e:
            logger.exception("Ошибка обработки файла")
            messages.error(
                request,
                f'Ошибка обработки файла: {str(e)}. '
                'Проверьте формат файла и скачайте пример.'
            )
            return render(request, template_name, context)

    return render(request, template_name, context)


@login_required
def complete_assignment(request, pk):
    """
    Обработка отметки о выполнении задания
    Доступно только оператору для своих заданий
    """
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    success, message = assignment.complete(request.user)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    # Перенаправляем обратно на страницу профиля пользователя
    return redirect('users:profile', username=request.user.username)
