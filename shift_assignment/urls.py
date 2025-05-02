from django.urls import path
from . import views
from .views import CompleteAssignmentView

app_name = 'shift_assignment'

urlpatterns = [
    # Основные CRUD операции
    path('', views.ShiftAssignmentListView.as_view(), name='list'),
    path('create/', views.ShiftAssignmentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ShiftAssignmentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ShiftAssignmentDeleteView.as_view(), name='delete'),

    # Архив и дополнительные функции
    path('archive/', views.ShiftAssignmentArchiveView.as_view(), name='archive'),
    path('upload/', views.upload_shift_assignments, name='upload'),

    # Альтернативные URL для совместимости (если нужно)
    path('update/<int:pk>/', views.ShiftAssignmentUpdateView.as_view(), name='old_update'),
    # Можно удалить после перехода
    path('delete/<int:pk>/', views.ShiftAssignmentDeleteView.as_view(), name='old_delete'),
    # Можно удалить после перехода
    path('detail/<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='old_detail'),
path('<int:pk>/complete/', CompleteAssignmentView.as_view(), name='complete'),
    # Можно удалить после перехода
]