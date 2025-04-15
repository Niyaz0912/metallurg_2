import pandas as pd
from django.shortcuts import redirect
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import ShiftAssignment
from .forms import ShiftAssignmentForm, UpdateShiftAssignmentForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User


class ShiftAssignmentListView(ListView):
    model = ShiftAssignment
    template_name = 'shift_assignment/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список сменных заданий'
        return context


class ShiftAssignmentCreateView(PermissionRequiredMixin, CreateView):
    model = ShiftAssignment
    form_class = ShiftAssignmentForm
    template_name = 'shift_assignment/create.html'
    permission_required = 'shift_assignment.add_shiftassignment'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ShiftAssignmentUpdateView(PermissionRequiredMixin, UpdateView):
    model = ShiftAssignment
    form_class = UpdateShiftAssignmentForm
    template_name = 'shift_assignment/update.html'
    permission_required = 'shift_assignment.change_shiftassignment'

    def form_valid(self, form):
        if form.instance.execution_status:
            # Переместить в архив
            form.instance.save()
            messages.success(self.request, 'Задание выполнено и перемещено в архив')
            return redirect('shift_assignment:archive')
        return super().form_valid(form)


class ShiftAssignmentDeleteView(PermissionRequiredMixin, DeleteView):
    model = ShiftAssignment
    template_name = 'shift_assignment/delete.html'
    success_url = reverse_lazy('shift_assignment:list')
    permission_required = 'shift_assignment.delete_shiftassignment'


class ShiftAssignmentDetailView(DetailView):
    model = ShiftAssignment
    template_name = 'shift_assignment/detail.html'


class ShiftAssignmentArchiveView(ListView):
    model = ShiftAssignment
    template_name = 'shift_assignment/archive.html'

    def get_queryset(self):
        return ShiftAssignment.objects.filter(execution_status=True)


def upload_shift_assignments(request):
    if request.method == 'POST':
        file = request.FILES['file']
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file)
            for index, row in df.iterrows():
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
                        part_blueprint=None,  # Не загружается из файла
                        comment=row['comment']
                    )
                except Exception as e:
                    messages.error(request, f'Ошибка при создании задания: {e}')
            messages.success(request, 'Задания успешно загружены')
            return redirect('shift_assignment:list')
        else:
            messages.error(request, 'Неправильный формат файла')
    return render(request, 'shift_assignment/upload.html')
