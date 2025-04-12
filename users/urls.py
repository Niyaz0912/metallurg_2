from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile'),
    path('shift_archive/<int:pk>/', views.ShiftArchiveView.as_view(), name='shift_archive'),
    path('shift_schedule/<int:pk>/', views.ShiftScheduleView.as_view(), name='shift_schedule'),
]
