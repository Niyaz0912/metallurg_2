import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required  # Добавлен импорт
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils import timezone  # Добавлен импорт
from .models import ShiftAssignment, ShiftAssignmentArchive
from .forms import ShiftAssignmentForm, UpdateShiftAssignmentForm

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
        return ShiftAssignment.objects.filter(execution_status=False).order_by('-date')

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
        raise PermissionDenied("У вас нет прав для загрузки заданий")

    template_name = 'shift_assignment/upload.html'
    context = {
        'title': 'Загрузка сменных заданий из Excel',
        'example_columns': [
            'customer (обязательно)',
            'date (обязательно, формат ДД.ММ.ГГГГ)',
            'machine_number (обязательно)',
            'operator (обязательно, имя пользователя)',
            'order (обязательно)',
            'part (обязательно)',
            'quantity (обязательно, число)',
            'comment (необязательно)'
        ]
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
            df = pd.read_excel(file)
            required_columns = ['customer', 'date', 'machine_number', 'operator',
                                'order', 'part', 'quantity']

            if not all(col in df.columns for col in required_columns):
                missing = set(required_columns) - set(df.columns)
                messages.error(request, f'Отсутствуют обязательные колонки: {", ".join(missing)}')
                return render(request, template_name, context)

            success_count = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    operator = User.objects.get(username=row['operator'])
                    ShiftAssignment.objects.create(
                        customer=row['customer'],
                        date=row['date'],
                        machine_number=row['machine_number'],
                        operator=operator,
                        order=row['order'],
                        part=row['part'],
                        quantity=row['quantity'],
                        comment=row.get('comment', ''),
                        created_by=request.user
                    )
                    success_count += 1
                except User.DoesNotExist:
                    errors.append(f'Строка {idx + 2}: Оператор "{row["operator"]}" не найден')
                except Exception as e:
                    errors.append(f'Строка {idx + 2}: {str(e)}')

            if success_count > 0:
                messages.success(request, f'Успешно загружено {success_count} заданий')
            if errors:
                messages.warning(request, f'Найдено {len(errors)} ошибок при обработке файла')
                for error in errors[:5]:  # Показываем первые 5 ошибок
                    messages.warning(request, error)
                if len(errors) > 5:
                    messages.warning(request, f'...и еще {len(errors) - 5} ошибок')

            return redirect('shift_assignment:list')

        except Exception as e:
            messages.error(request, f'Ошибка обработки файла: {str(e)}')
            return render(request, template_name, context)

    return render(request, template_name, context)