from django.urls import path
from .views import (
    ProductionPlanListView,
    ProductionPlanCreateView,
    ProductionPlanUpdateView,
    ProductionPlanDeleteView,
    ProductionPlanDetailView,
    # upload_production_plans удалён
)

app_name = 'production_plan'

urlpatterns = [
    path('', ProductionPlanListView.as_view(), name='list'),
    path('create/', ProductionPlanCreateView.as_view(), name='create'),
    path('<int:pk>/', ProductionPlanDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', ProductionPlanUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', ProductionPlanDeleteView.as_view(), name='delete'),
    # path('upload/', upload_production_plans, name='upload'),  # удалено
]
