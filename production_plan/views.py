from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import ProductionPlan
from .forms import ProductionPlanForm
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ProductionPlanListView(LoginRequiredMixin, ListView):
    model = ProductionPlan
    template_name = 'production_plan/list.html'
    context_object_name = 'object_list'


class StaffRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role in ['admin', 'director']:
            return redirect('production_plan:list')
        return super().dispatch(request, *args, **kwargs)


class ProductionPlanCreateView(StaffRequiredMixin, CreateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/create.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = 'production_plan/update.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductionPlan
    template_name = 'production_plan/delete.html'
    success_url = reverse_lazy('production_plan:list')


class ProductionPlanDetailView(LoginRequiredMixin, DetailView):
    model = ProductionPlan
    template_name = 'production_plan/detail.html'

