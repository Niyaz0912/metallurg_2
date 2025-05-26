from django.urls import path
from . import views

app_name = 'shift_assignment'

urlpatterns = [
    path('active/', views.ActiveAssignmentsView.as_view(), name='active'),
    path('completed/', views.CompletedAssignmentsView.as_view(), name='completed'),
    path('create/', views.ShiftAssignmentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ShiftAssignmentDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ShiftAssignmentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ShiftAssignmentDeleteView.as_view(), name='delete'),
    path('<int:pk>/complete/', views.CompleteAssignmentView.as_view(), name='complete'),
    path('upload/', views.ShiftAssignmentUploadView.as_view(), name='upload'),
    path('download_template/', views.download_rus_template, name='download_template'),
    path('delete-all/', views.delete_all_assignments, name='delete_all'),
]


