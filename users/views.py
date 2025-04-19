from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, DetailView
from django.urls import reverse_lazy
from users.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from production_plan.models import ProductionPlan, Supply
from shift_assignment.models import MachineStatus, ShiftAssignment


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == 'admin':
            return reverse_lazy('production_plan:list')
        elif user.role in ['director', 'master']:
            return reverse_lazy('production_plan:list')
        else:
            return reverse_lazy('users:profile', kwargs={'pk': user.pk})


class CustomLogoutView(LogoutView):
    template_name = 'users/logout.html'
    next_page = 'login'


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['current_user'] = user

        # Данные для оператора
        if user.role == 'operator':
            context['current_assignment'] = ShiftAssignment.objects.filter(
                operator=user,
                execution_status=False
            ).first()

        # Данные для мастера
        elif user.role == 'master':
            context['machine_statuses'] = MachineStatus.objects.all()
            context['recent_assignments'] = ShiftAssignment.objects.filter(
                execution_status=True
            ).select_related('operator').order_by('-updated_at')[:10]

        # Данные для администратора и директора
        elif user.role in ['admin', 'director']:
            context['active_plans'] = ProductionPlan.objects.filter(
                is_completed=False
            ).order_by('-deadline')[:5]
            context['recent_completed_plans'] = ProductionPlan.objects.filter(
                is_completed=True
            ).order_by('-deadline')[:5]
            context['upcoming_supplies'] = Supply.objects.filter(
                status='pending'
            ).order_by('expected_date')[:5]  # Исправлено delivery_date на expected_date
            context['recent_received_supplies'] = Supply.objects.filter(
                status='received'
            ).order_by('-received_date')[:5]  # Исправлено receipt_date на received_date

        return context


class ShiftArchiveView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/shift_archive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == 'operator':
            context['assignment_history'] = ShiftAssignment.objects.filter(
                operator=user
            ).order_by('-date')[:20]
        else:
            context['assignment_history'] = ShiftAssignment.objects.select_related(
                'operator'
            ).order_by('-date')[:50]

        return context


class ShiftScheduleView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/shift_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Здесь будет логика для графика смен
        return context
