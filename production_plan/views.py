from django.shortcuts import redirect
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import ProductionPlan
from .forms import ProductionPlanForm
from django.urls import reverse_lazy


class ProductionPlanListView(PermissionRequiredMixin, ListView):
    model = ProductionPlan
    template_name = 'production_plan/list.html'
    permission_required = 'production_plan.view_productionplan'
    login_url = '/users/login/'  # Укажите URL вашей страницы входа

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Список производственных планов'
        return context


class ProductionPlanCreateView(PermissionRequiredMixin, CreateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/create.html'
    permission_required = 'production_plan.add_productionplan'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductionPlanUpdateView(PermissionRequiredMixin, UpdateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/update.html'
    permission_required = 'production_plan.change_productionplan'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ProductionPlanDeleteView(PermissionRequiredMixin, DeleteView):
    model = ProductionPlan
    template_name = 'production_plan/delete.html'
    success_url = reverse_lazy('production_plan:list')
    permission_required = 'production_plan.delete_productionplan'


class ProductionPlanDetailView(PermissionRequiredMixin, DetailView):
    model = ProductionPlan
    template_name = 'production_plan/detail.html'
    permission_required = 'production_plan.view_productionplan'
