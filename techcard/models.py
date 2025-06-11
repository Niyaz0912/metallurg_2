from django.db import models
from django.db.models import Sum
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
        verbose_name='Марка стали',
        blank=True,
        default='Н/Д',  # "Не определено" по умолчанию
        help_text='Оставьте пустым, если марка стали не имеет значения'
    )
    total_quantity = models.PositiveIntegerField(
        verbose_name='Количество (шт)'
    )
    technological_process = models.TextField(
        verbose_name='Технологический маршрут',
        help_text='Последовательность операций с параметрами'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_quantity(self):
        """Оставшееся количество продукции к выпуску."""
        return max(0, self.total_quantity - self.production_plan.completed_quantity)  # Защита от отрицательных значений

    @property
    def progress(self):
        """Прогресс выполнения в процентах (0-100)."""
        if self.total_quantity == 0:
            return 0  # Избегаем деления на ноль
        return min(100, round((self.production_plan.completed_quantity / self.total_quantity) * 100, 1))

    def __str__(self):
        return f"Техкарта #{self.id} ({self.production_plan})"


class TechCardStage(models.Model):
    techcard = models.ForeignKey(
        TechCard,
        on_delete=models.CASCADE,
        related_name='stages',
        verbose_name='Техкарта'
    )
    name = models.CharField(max_length=200, verbose_name='Название этапа')
    equipment = models.CharField(max_length=200, verbose_name='Оборудование')
    operation_time = models.DurationField(verbose_name='Время операции', null=True, blank=True)
    instructions = models.TextField(verbose_name='Инструкция', blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок этапа')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.name}"
