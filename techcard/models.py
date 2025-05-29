from django.db import models
from production_plan.models import ProductionPlan
from shift_assignment.models import ShiftAssignment


class TechCard(models.Model):
    production_plan = models.OneToOneField(
        ProductionPlan,
        on_delete=models.CASCADE,
        related_name='techcard',
        verbose_name='Производственный план'
    )
    drawing = models.FileField(
        upload_to='techcards/%Y/%m/%d/',
        verbose_name='Чертеж/Схема',
        blank=True,
        null=True
    )
    steel_grade = models.CharField(
        max_length=100,
        verbose_name='Марка стали'
    )
    total_quantity = models.PositiveIntegerField(
        verbose_name='План выпуска (шт)'
    )
    technological_process = models.TextField(
        verbose_name='Технологический маршрут',
        help_text='Последовательность операций с параметрами'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_quantity(self):
        completed = self.production_plan.shift_assignments.filter(
            status=ShiftAssignment.Status.COMPLETED
        ).aggregate(total=models.Sum('actual_quantity'))['total'] or 0
        return self.total_quantity - completed

    def __str__(self):
        return f"Техкарта #{self.id} ({self.production_plan})"
