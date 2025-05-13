from django.urls import path
from .views import (
    ProductionPlanListView,
    ProductionPlanUpdateView,
    ProductionPlanDeleteView,
    ProductionPlanDetailView,
    ProductionPlanCreateView,
    ProductionPlanUploadView, download_production_plan_template,
)

app_name = 'production_plan'

urlpatterns = [
    path('', ProductionPlanListView.as_view(), name='list'),
    path('create/', ProductionPlanCreateView.as_view(), name='create'),
    path('update/<int:pk>/', ProductionPlanUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ProductionPlanDeleteView.as_view(), name='delete'),
    path('detail/<int:pk>/', ProductionPlanDetailView.as_view(), name='detail'),
    path('upload/', ProductionPlanUploadView.as_view(), name='upload'),
    path('download_template/', download_production_plan_template, name='download_template'),
]
