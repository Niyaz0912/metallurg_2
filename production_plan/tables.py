import django_tables2 as tables
from .models import ProductionPlan

class ProductionPlanTable(tables.Table):
    class Meta:
        model = ProductionPlan
        template_name = "django_tables2/bootstrap.html"  # или свой шаблон
        fields = ('customer', 'order_name', 'product', 'quantity', 'deadline')
