from django.shortcuts import redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import ProductionPlan
from .forms import ProductionPlanForm
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == 'admin':
            return redirect('admin:index')
        elif request.user.role in ['director', 'master']:
            return redirect('production:list')
        return redirect('shifts:list')


class StaffRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки ролей admin и director"""

    def test_func(self):
        return self.request.user.role in ['admin', 'director']

    def handle_no_permission(self):
        return redirect('production_plan:list')


class ProductionPlanListView(LoginRequiredMixin, ListView):
    model = ProductionPlan
    template_name = 'production_plan/list.html'
    login_url = '/users/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список производственных планов'
        context['can_edit'] = self.request.user.role in ['admin', 'director']
        return context


class ProductionPlanCreateView(StaffRequiredMixin, CreateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/create.html'
    success_url = reverse_lazy('production_plan:list')  # Перенаправление после создания

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Дополнительная логика перенаправления при необходимости"""
        # Можно добавить сообщение об успешном создании
        # messages.success(self.request, "Производственный план успешно создан")
        return super().get_success_url()


class ProductionPlanUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/update.html'
    success_url = reverse_lazy('production_plan:list')  # Перенаправление после обновления

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Альтернативный вариант - перенаправление на детали плана"""
        # return reverse_lazy('production_plan:detail', kwargs={'pk': self.object.pk})
        return super().get_success_url()


class ProductionPlanDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductionPlan
    template_name = 'production_plan/delete.html'
    success_url = reverse_lazy('production_plan:list')

    def delete(self, request, *args, **kwargs):
        """Дополнительная логика перед удалением"""
        # Можно добавить сообщение об успешном удалении
        # messages.success(self.request, "План успешно удален")
        return super().delete(request, *args, **kwargs)


class ProductionPlanDetailView(LoginRequiredMixin, DetailView):
    model = ProductionPlan
    template_name = 'production_plan/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.role in ['admin', 'director']
        return context
