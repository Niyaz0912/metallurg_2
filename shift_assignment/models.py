from django.db import models
from django.conf import settings
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


class ShiftAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNMENT = 'assignment', 'Задание на смену'
        COMPLETED = 'completed', 'Выполненное задание'

    class ShiftType(models.TextChoices):
        DAY = 'day', 'Дневная смена (08:00-20:00)'
        NIGHT = 'night', 'Ночная смена (20:00-08:00)'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNMENT,
        verbose_name='Статус задания',
        db_index=True
    )
    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.CASCADE,
        related_name='shift_assignments',
        verbose_name='План производства'
    )
    shift_date = models.DateField(
        verbose_name='Дата смены',
        default=timezone.now,
        db_index=True
    )
    shift_type = models.CharField(
        max_length=10,
        choices=ShiftType.choices,
        default=ShiftType.DAY,
        verbose_name='Тип смены'
    )
    machine_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Номер станка'
    )
    order_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Наименование изделия'
    )
    work_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Вид работ'
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='shift_assignments',
        verbose_name='Оператор'
    )
    planned_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Плановое количество'
    )
    actual_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Фактическое количество'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
    )
    drawing = models.FileField(
        upload_to='drawings/%Y/%m/%d/',
        verbose_name='Операционно-технологическая карта',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения',
        db_index=True
    )

    def complete(self, actual_quantity, user):
        """
        Завершает задание и обновляет статус
        """
        if self.status == self.Status.COMPLETED:
            return False, "Задание уже завершено"

        if not actual_quantity or actual_quantity <= 0:
            return False, "Укажите фактическое количество"

        self.actual_quantity = actual_quantity
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['actual_quantity', 'status', 'completed_at'])

        # Логирование действия
        logger.info(f"User {user.username} completed assignment {self.id}")
        return True, "Задание успешно завершено"

    def __str__(self):
        return f"{self.shift_date} {self.get_shift_type_display()} - Станок #{self.machine_number} ({self.operator})"

    @property
    def remaining_quantity(self):
        total = self.production_plan.techcard.total_quantity if hasattr(self.production_plan, 'techcard') else 0
        # Суммируем фактическое количество по всем выполненным сменам (например, по оператору или по плану)
        from django.db.models import Sum

        completed_qty = ShiftAssignment.objects.filter(
            production_plan=self.production_plan,
            status=ShiftAssignment.Status.COMPLETED
        ).aggregate(total=Sum('actual_quantity'))['total'] or 0

        remaining = total - completed_qty
        return max(remaining, 0)

    class Meta:
        verbose_name = 'Сменное задание'
        verbose_name_plural = 'Сменные задания'
        ordering = ['-shift_date', 'shift_type', 'machine_number']
        indexes = [
            models.Index(fields=['shift_date']),
            models.Index(fields=['operator']),
            models.Index(fields=['status']),
            models.Index(fields=['completed_at']),
        ]

