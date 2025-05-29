from django.contrib import admin
from .models import TechCard


@admin.register(TechCard)
class TechCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'production_plan', 'steel_grade', 'total_quantity', 'created_at')
    search_fields = ('production_plan__customer', 'steel_grade')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
