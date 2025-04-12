from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import View, TemplateView, FormView, DetailView
from .forms import LoginForm, RegistrationForm
from .models import User
from django.urls import reverse_lazy


class LoginView(FormView):
    template_name = 'users/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            return redirect('users:profile', pk=user.pk)
        else:
            messages.error(self.request, 'Неправильное имя пользователя или пароль')
            return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('users:login')


class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        return redirect('users:profile', pk=user.pk)


class ProfileView(DetailView):
    model = User
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Логика для карточки с заданием на смену
        # Здесь вы можете получить задание из базы данных и отобразить его
        shift_task = None  # Получите задание из базы данных
        context['shift_task'] = shift_task
        return context


class ShiftArchiveView(DetailView):
    model = User
    template_name = 'users/shift_archive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Логика для отображения архива смен
        # Здесь вы можете получить архив смен из базы данных и отобразить его
        shift_archive = None  # Получите архив смен из базы данных
        context['shift_archive'] = shift_archive
        return context


class ShiftScheduleView(DetailView):
    model = User
    template_name = 'users/shift_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Логика для отображения графика смен
        # Здесь вы можете получить график смен из базы данных и отобразить его
        shift_schedule = None  # Получите график смен из базы данных
        context['shift_schedule'] = shift_schedule
        return context
