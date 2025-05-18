from django.contrib import admin
from .models import ShiftAssignment


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shift_date', 'operator', 'status', 'completed_at')
    list_filter = ('status', 'shift_type', 'operator')
    search_fields = ('order_name', 'machine_number')
    date_hierarchy = 'shift_date'

    def get_customer(self, obj):
        # Предполагается, что у production_plan есть поле customer
        return obj.production_plan.customer if obj.production_plan else '-'

    get_customer.short_description = 'Клиент'
    get_customer.admin_order_field = 'production_plan__customer'

