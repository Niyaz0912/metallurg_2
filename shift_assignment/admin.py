from django.contrib import admin
from .models import ShiftAssignment, ShiftAssignmentArchive


class ShiftAssignmentAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели сменных заданий"""
    list_display = (
        'id', 'customer', 'date', 'machine_number', 'operator',
        'quantity', 'execution_status'
    )
    list_filter = (
        'execution_status', 'date', 'machine_number', 'operator'
    )
    search_fields = (
        'customer', 'operator__username'
    )
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'customer', 'date', 'machine_number', 'operator',
                'quantity', 'part_blueprint'
            )
        }),
        ('Дополнительно', {
            'fields': (
                'execution_status', 'comment',
                'created_at', 'updated_at'
            )
        }),
    )


class ShiftAssignmentArchiveAdmin(admin.ModelAdmin):
    """Административный интерфейс для архива сменных заданий"""
    list_display = (
        'original_id', 'customer', 'date', 'machine_number', 'operator',
        'order', 'part', 'quantity', 'actual_quantity',
        'quality_check', 'completed_at'
    )
    list_filter = (
        'date', 'machine_number', 'operator', 'quality_check'
    )
    search_fields = (
        'customer', 'order', 'part', 'operator__username'
    )
    readonly_fields = (
        'original_id', 'completed_at', 'shift_duration'
    )
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'original_id', 'customer', 'date', 'machine_number',
                'operator', 'order', 'part', 'quantity', 'part_blueprint'
            )
        }),
        ('Результаты выполнения', {
            'fields': (
                'actual_quantity', 'quality_check', 'shift_duration'
            )
        }),
        ('Дополнительно', {
            'fields': (
                'comment', 'completed_at'
            )
        }),
    )


admin.site.register(ShiftAssignment, ShiftAssignmentAdmin)
admin.site.register(ShiftAssignmentArchive, ShiftAssignmentArchiveAdmin)
