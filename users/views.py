from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, DetailView
from django.urls import reverse_lazy
from users.models import User


class CustomLoginView(LoginView):
    template_name = 'users/login.html'  # Ваш шаблон
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.role == 'admin':
            return reverse_lazy('admin:index')
        elif self.request.user.role in ['director', 'master']:
            return reverse_lazy('production_plan:list')
        return reverse_lazy('shifts:list')


class CustomLogoutView(LogoutView):
    template_name = 'users/logout.html'  # Ваш шаблон
    next_page = 'login'


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'users/register.html'  # Ваш шаблон
    success_url = reverse_lazy('login')


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
