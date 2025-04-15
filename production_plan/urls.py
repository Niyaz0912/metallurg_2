from django.urls import path
from . import views

app_name = 'production_plan'

urlpatterns = [
    path('', views.ProductionPlanListView.as_view(), name='list'),
    path('create/', views.ProductionPlanCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.ProductionPlanUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.ProductionPlanDeleteView.as_view(), name='delete'),
    path('detail/<int:pk>/', views.ProductionPlanDetailView.as_view(), name='detail'),
]
