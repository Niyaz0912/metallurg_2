from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView, RegisterView, LegacyProfileRedirectView

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Новые URL с username
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('shift_archive/<str:username>/', views.ShiftArchiveView.as_view(), name='shift_archive'),
    path('profile/<str:username>/update/', views.UserUpdateView.as_view(), name='update'),

    # Старые URL с ID для обратной совместимости
    path('profile/<int:pk>/', LegacyProfileRedirectView.as_view(), name='legacy_profile'),
    path('shift_archive/<int:pk>/', views.LegacyShiftArchiveRedirectView.as_view(), name='legacy_shift_archive'),

    path('shift_schedule/', views.ShiftScheduleView.as_view(), name='shift_schedule'),
]

