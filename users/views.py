from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import (
    CreateView,
    DetailView,
    UpdateView,
    TemplateView,
    RedirectView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .forms import RegistrationForm, UserUpdateForm
from .models import User
from shift_assignment.models import ShiftAssignment


class RoleRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки роли пользователя"""
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас нет прав для просмотра этой страницы")
        return super().handle_no_permission()


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'username': self.request.user.username})


class CustomLogoutView(LogoutView):
    next_page = 'login'


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_user = self.get_object()

        if user.role == 'operator' and user == profile_user:
            context['active_assignments'] = ShiftAssignment.objects.filter(
                operator__username=user.username,
                status=False
            ).order_by('-shift_date')

            context['completed_assignments'] = ShiftAssignment.objects.filter(
                operator__username=user.username,
                status=True
            ).order_by('-completed_at')[:10]

        elif user.role in ['master', 'director']:
            context['active_assignments'] = ShiftAssignment.objects.filter(
                status=False
            ).order_by('-shift_date')

            context['completed_assignments'] = ShiftAssignment.objects.filter(
                status=True
            ).order_by('-completed_at')[:10]

        return context


class LegacyProfileRedirectView(LoginRequiredMixin, RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        return reverse('users:profile', kwargs={'username': user.username})


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/update.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'username': self.object.username})


class ShiftArchiveView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/shift_archive.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_user = self.get_object()

        if user.role == 'operator' and user == profile_user:
            context['assignments'] = ShiftAssignment.objects.filter(
                operator=user
            ).order_by('-shift_date')[:20]
        elif user.role in ['master', 'director', 'admin']:
            context['assignments'] = ShiftAssignment.objects.select_related(
                'operator'
            ).order_by('-shift_date')[:50]

        return context


class LegacyShiftArchiveRedirectView(LoginRequiredMixin, RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        return reverse('users:shift_archive', kwargs={'username': user.username})


class ShiftScheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'users/shift_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == 'operator':
            context['schedule'] = ShiftAssignment.objects.filter(
                operator=user,
                date__gte=timezone.now().date()
            ).order_by('date')[:7]
        elif user.role in ['master', 'director', 'admin']:
            context['schedule'] = ShiftAssignment.objects.filter(
                date__gte=timezone.now().date()
            ).select_related('operator').order_by('date', 'machine_number')[:14]

        return context
