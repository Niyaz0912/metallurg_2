from django.urls import include, path
from django.contrib import admin
from django.views.generic import RedirectView  # Для перенаправления с корня

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Главная страница (перенаправление на логин или другую стартовую страницу)
    path('', RedirectView.as_view(url='login/'), name='home'),

    # Приложение users (включает login/, register/, profile/ и т.д.)
    path('', include('users.urls')),

    # Приложение production_plan
    path('production_plan/', include('production_plan.urls')),

    # Приложение shift_assignment
    path('shift_assignment/', include('shift_assignment.urls')),

    # Дополнительно: можно добавить страницу 404 для DEBUG=False
    # handler404 = 'users.views.custom_404_view'
]