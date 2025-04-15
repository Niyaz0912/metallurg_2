from django.urls import path
from . import views

app_name = 'shift_assignment'

urlpatterns = [
    path('', views.ShiftAssignmentListView.as_view(), name='list'),
    path('create/', views.ShiftAssignmentCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.ShiftAssignmentUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.ShiftAssignmentDeleteView.as_view(), name='delete'),
    path('detail/<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='detail'),
    path('archive/', views.ShiftAssignmentArchiveView.as_view(), name='archive'),
    path('upload/', views.upload_shift_assignments, name='upload'),
]
