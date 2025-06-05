from django.urls import path
from . import views
from .views import (
    TechCardListView, TechCardCreateView, TechCardDetailView,
    TechCardUpdateView, TechCardDeleteView,
    TechCardStageCreateView,
)

app_name = 'techcard'

urlpatterns = [
    path('', TechCardListView.as_view(), name='list'),
    path('create/', TechCardCreateView.as_view(), name='create'),
    path('<int:pk>/', TechCardDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', TechCardUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', TechCardDeleteView.as_view(), name='delete'),

    # Добавление этапа к техкарте
    path('<int:techcard_pk>/stage/add/', TechCardStageCreateView.as_view(), name='stage_add'),
]

