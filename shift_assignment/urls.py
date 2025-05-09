from django.urls import path
from . import views
from .views import CompleteAssignmentView

app_name = 'shift_assignment'

urlpatterns = [
    path('', views.ShiftAssignmentListView.as_view(), name='list'),
    path('create/', views.ShiftAssignmentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ShiftAssignmentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ShiftAssignmentDeleteView.as_view(), name='delete'),

    path('archive/', views.ShiftAssignmentArchiveView.as_view(), name='archive'),
    path('upload/', views.upload_shift_assignments, name='upload'),

    path('update/<int:pk>/', views.ShiftAssignmentUpdateView.as_view(), name='old_update'),  # устаревшие, можно удалить
    path('delete/<int:pk>/', views.ShiftAssignmentDeleteView.as_view(), name='old_delete'),  # устаревшие, можно удалить
    path('detail/<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='old_detail'),  # устаревшие, можно удалить
    path('<int:pk>/complete/', CompleteAssignmentView.as_view(), name='complete'),
]
