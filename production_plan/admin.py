from django.contrib import admin
from .models import ProductionPlan


class ProductionPlanAdmin(admin.ModelAdmin):
    pass


admin.site.register(ProductionPlan, ProductionPlanAdmin)
