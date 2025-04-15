from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from users.views import CustomLoginView, CustomLogoutView, RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Главная страница
    path('', RedirectView.as_view(pattern_name='login'), name='home'),

    # Аутентификация
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Приложения
    path('users/', include('users.urls')),
    path('production_plan/', include('production_plan.urls', namespace='production_plan')),
    path('shifts/', include('shift_assignment.urls', namespace='shift_assignment')),
]