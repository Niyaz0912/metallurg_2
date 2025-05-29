from django.urls import path
from .views import TechCardDetailView

app_name = 'techcard'

urlpatterns = [
    path('<int:pk>/', TechCardDetailView.as_view(), name='detail'),
]
