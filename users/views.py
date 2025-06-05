
from django.views.generic import ListView
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
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .forms import RegistrationForm, UserUpdateForm
from .models import User
from shift_assignment.models import ShiftAssignment
from production_plan.models import ProductionPlan
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings


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


class RegisterView(UserPassesTestMixin, CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def test_func(self):
        return self.request.user.is_superuser  # доступ только суперпользователю

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Доступ запрещён")


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'  # Главный шаблон-обертка
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_user = self.get_object()  # Это ключевая строка

        context.update({
            'profile_user': profile_user,
            'can_edit_profile': user == profile_user or user.is_superuser,
        })

        # Получаем данные заданий
        context.update(self._get_assignment_data(user, profile_user))

        # Добавляем фильтры для администраторов
        if user.role in ['master', 'director', 'admin']:
            context.update(self._get_filter_data())

        role = profile_user.role if profile_user else None

        role_templates = {
            'admin': 'users/profile_parts/admin.html',
            'master': 'users/profile_parts/master.html',
            'director': 'users/profile_parts/director.html',
            'operator': 'users/profile_parts/operator.html',
        }

        context['role_template'] = role_templates.get(role, 'users/roles/default.html')

        return context

    def _get_filter_data(self):
        """Данные для фильтров (общие для мастеров/директоров/админов)"""
        return {
            'operators': User.objects.filter(role='operator').order_by('last_name'),
            'customers': ProductionPlan.objects.filter(
                shift_assignments__status=ShiftAssignment.Status.COMPLETED
            ).values_list('customer', flat=True).distinct().order_by('customer'),
            'machines': ShiftAssignment.objects.exclude(
                Q(machine_number__isnull=True) | Q(machine_number__exact='')
            ).values_list('machine_number', flat=True).distinct().order_by('machine_number'),
        }

    def _get_assignment_data(self, user, profile_user):
        """Данные заданий с учетом роли и фильтров"""
        data = {}

        # Базовые querysets
        active_assignments = ShiftAssignment.objects.filter(
            status='assignment'
        ).select_related('production_plan', 'operator')

        completed_assignments = ShiftAssignment.objects.filter(
            status='completed'
        ).select_related('production_plan', 'operator')

        # Логика для оператора
        if user.role == 'operator' or profile_user.role == 'operator':
            active_assignments = active_assignments.filter(operator=profile_user)
            completed_assignments = completed_assignments.filter(operator=profile_user)

        # Логика для мастера/директора/админа
        elif user.role in ['master', 'director', 'admin']:
            # Если смотрим свой профиль - показываем все задания
            if user == profile_user:
                completed_assignments = self._apply_filters(completed_assignments)
            # Если смотрим профиль оператора - показываем его задания
            elif profile_user.role == 'operator':
                active_assignments = active_assignments.filter(operator=profile_user)
                completed_assignments = completed_assignments.filter(operator=profile_user)
            # Иначе применяем общие фильтры
            else:
                completed_assignments = self._apply_filters(completed_assignments)

        # Сортировка и ограничение
        data['active_assignments'] = active_assignments.order_by('-shift_date')
        data['completed_assignments'] = completed_assignments.order_by('-completed_at')[:50]
        data['completed_assignments_count'] = completed_assignments.count()

        return data

    def _apply_filters(self, queryset):
        """Применение фильтров из GET-параметров"""
        filters = Q()
        request = self.request

        # Фильтр по оператору
        if operator := request.GET.get('operator'):
            filters &= Q(operator__username=operator)

        # Фильтр по заказчику
        if customer := request.GET.get('customer'):
            filters &= Q(production_plan__customer=customer)

        # Фильтр по станку
        if machine := request.GET.get('machine'):
            filters &= Q(machine_number=machine)

        # Фильтр по датам
        if date_from := request.GET.get('date_from'):
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                filters &= Q(shift_date__gte=date_from)
            except ValueError:
                pass

        if date_to := request.GET.get('date_to'):
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                filters &= Q(shift_date__lte=date_to)
            except ValueError:
                pass

        return queryset.filter(filters)


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


class OperatorListView(ListView):
    model = User
    template_name = 'users/operator_list.html'  # создадим этот шаблон
    context_object_name = 'operators'

    def get_queryset(self):
        # Возвращаем только пользователей с ролью 'operator'
        return User.objects.filter(role='operator').order_by('username')


def request_access(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        contact = request.POST.get('contact', '').strip()

        if not all([full_name, employee_id, contact]):
            messages.error(request, 'Пожалуйста, заполните все поля')
            return render(request, 'users/request_access.html')

        try:
            send_mail(
                subject=f'Запрос доступа от {full_name}',
                message=(
                    f'Детали запроса:\n\n'
                    f'ФИО: {full_name}\n'
                    f'Табельный номер: {employee_id}\n'
                    f'Контактные данные: {contact}\n\n'
                    f'Дата запроса: {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.IT_SUPPORT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Ваш запрос отправлен. С вами свяжутся в ближайшее время.')
            return redirect('users:login')

        except Exception as e:
            messages.error(request, f'Ошибка при отправке запроса: {str(e)}')
            return render(request, 'users/request_access.html')

    return render(request, 'users/request_access.html')


def hr_contacts(request):
    return render(request, 'users/hr_contacts.html')