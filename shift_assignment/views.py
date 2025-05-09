import logging

import pandas as pd
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages

from .models import ShiftAssignment, ShiftAssignmentArchive
from users.models import User
from .forms import ShiftAssignmentForm, UpdateShiftAssignmentForm
from django.utils.translation import gettext as _


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
                status='active'
            ).order_by('-shift_date')

        # Для мастеров/директоров - все активные задания
        return ShiftAssignment.objects.filter(
            status='active'
        ).order_by('-shift_date')

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
        if form.instance.status == 'completed' and not form.instance.completed_at:
            form.instance.completed_at = timezone.now()
            ShiftAssignmentArchive.objects.create_from_assignment(form.instance)
            messages.success(self.request, 'Задание выполнено и перемещено в архив')
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.status == 'completed':
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
        raise PermissionDenied(_("Только мастер или директор могут загружать задания"))

    template_name = 'shift_assignment/upload.html'
    context = {
        'title': _('Загрузка сменных заданий из Excel'),
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
            messages.error(request, _('Файл не выбран'))
            return render(request, template_name, context)

        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, _('Поддерживаются только файлы Excel (.xlsx, .xls)'))
            return render(request, template_name, context)

        try:
            df = pd.read_excel(file)

            operator_col = None
            for col in ['operator', 'operator_id']:
                if col in df.columns:
                    operator_col = col
                    break

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
                    _('Отсутствуют обязательные колонки: ') + ", ".join(missing_columns)
                )
                return render(request, template_name, context)

            success_count = 0
            errors = []
            duplicates = 0

            for idx, row in df.iterrows():
                try:
                    if pd.isna(row['customer']) or not str(row['customer']).strip():
                        raise ValueError(_("Не указан клиент"))

                    if pd.isna(row[operator_col]):
                        raise ValueError(_("Не указан оператор"))

                    operator = User.objects.get(username=row[operator_col])

                    # Поиск production_plan по order и customer (предполагается, что есть такая модель и поля)
                    production_plan = None
                    from production_plan.models import ProductionPlan
                    try:
                        production_plan = ProductionPlan.objects.get(
                            order=row['order'],
                            customer=row['customer']
                        )
                    except ProductionPlan.DoesNotExist:
                        raise ValueError(_("План производства с таким заказом и клиентом не найден"))

                    # Проверка дубликатов
                    if ShiftAssignment.objects.filter(
                        shift_date=row['date'],
                        machine_number=row['machine_number'],
                        operator=operator,
                        production_plan=production_plan
                    ).exists():
                        duplicates += 1
                        continue

                    ShiftAssignment.objects.create(
                        production_plan=production_plan,
                        shift_date=row['date'],
                        machine_number=str(row['machine_number']),
                        operator=operator,
                        planned_quantity=int(row['quantity']),
                        notes=row.get('comment', ''),
                        status=ShiftAssignment.Status.PLANNED,
                        shift_type=ShiftAssignment.ShiftType.DAY  # Можно расширить логику, если нужно
                    )
                    success_count += 1

                except User.DoesNotExist:
                    errors.append(_('Строка {0}: Оператор "{1}" не найден').format(idx + 2, row[operator_col]))
                except ValueError as e:
                    errors.append(_('Строка {0}: {1}').format(idx + 2, str(e)))
                except Exception as e:
                    errors.append(_('Строка {0}: Ошибка - {1}').format(idx + 2, str(e)))

            if success_count > 0:
                messages.success(request, _('Успешно загружено {0} заданий').format(success_count))

            if duplicates > 0:
                messages.warning(request, _('Пропущено {0} дубликатов (задания уже существуют)').format(duplicates))

            if errors:
                messages.error(request, _('Найдено {0} ошибок. Первые 5:').format(len(errors)))
                for error in errors[:5]:
                    messages.error(request, error)
                logger.error(f"Ошибки при загрузке файла {file.name}: {errors}")

            return redirect('shift_assignment:list')

        except Exception as e:
            logger.exception("Ошибка обработки файла")
            messages.error(
                request,
                _('Ошибка обработки файла: {0}. Проверьте формат файла и скачайте пример.').format(str(e))
            )
            return render(request, template_name, context)

    return render(request, template_name, context)


@login_required
def complete_assignment(request, pk):
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    success, message = assignment.complete(request.user)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('users:profile', username=request.user.username)

