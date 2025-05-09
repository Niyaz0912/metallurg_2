from django.contrib import admin
from .models import ShiftAssignment, ShiftAssignmentArchive


class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('get_customer', 'shift_date', 'planned_quantity', 'status')

    def get_customer(self, obj):
        # Предполагается, что у production_plan есть поле customer
        return obj.production_plan.customer if obj.production_plan else '-'

    get_customer.short_description = 'Клиент'
    get_customer.admin_order_field = 'production_plan__customer'

    list_filter = ('status', 'shift_date')


class ShiftAssignmentArchiveAdmin(admin.ModelAdmin):
    list_display = (
        'get_customer', 'shift_date', 'planned_quantity', 'quality_status', 'archived_at'
    )

    def get_customer(self, obj):
        return obj.production_plan.customer if obj.production_plan else '-'

    get_customer.short_description = 'Клиент'
    get_customer.admin_order_field = 'production_plan__customer'

    list_filter = ('shift_date', 'quality_status')
    readonly_fields = ('archived_at',)


admin.site.register(ShiftAssignment, ShiftAssignmentAdmin)
admin.site.register(ShiftAssignmentArchive, ShiftAssignmentArchiveAdmin)
