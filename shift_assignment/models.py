from datetime import date
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ShiftAssignment(models.Model):
    class ShiftType(models.TextChoices):
        DAY = 'day', _('Дневная смена (08:00-20:00)')
        NIGHT = 'night', _('Ночная смена (20:00-08:00)')

    class Status(models.TextChoices):
        ASSIGNMENT = 'assignment', _('Задание на смену')
        COMPLETED = 'completed', _('Выполненное задание')

    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.CASCADE,
        related_name='shift_assignments',
        verbose_name=_('План производства')
    )
    shift_date = models.DateField(
        verbose_name=_('Дата смены'),
        default=timezone.now,
        db_index=True
    )
    shift_type = models.CharField(
        max_length=10,
        choices=ShiftType.choices,
        verbose_name=_('Тип смены'),
        default=ShiftType.DAY
    )
    machine_number = models.CharField(
        max_length=50,
        verbose_name=_('Номер станка'),
        blank=True,
        null=True,
    )
    order_name = models.CharField(
        max_length=255,
        verbose_name=_('Наименование изделия'),
        blank=True,
        null=True,
    )
    work_type = models.CharField(
        max_length=255,
        verbose_name=_('Вид работ'),
        blank=True,
        null=True,
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='shift_assignments',
        verbose_name=_('Оператор'),
        limit_choices_to={'groups__name': 'Operators'}
    )
    planned_quantity = models.PositiveIntegerField(
        verbose_name=_('Плановое количество'),
        default=0
    )
    actual_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Фактическое количество')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNMENT,
        verbose_name=_('Статус задания'),
        db_index=True
    )
    drawing = models.FileField(
        upload_to='drawings/%Y/%m/%d/',
        verbose_name=_('Чертеж'),
        blank=True,
        null=True
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Завершил'),
        related_name='completed_shift_assignments'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата выполнения')
    )

    def complete_assignment(self, actual_quantity, user):
        if actual_quantity <= 0:
            return False, "Количество должно быть положительным числом"
        self.actual_quantity = actual_quantity
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()
        return True, "Задание успешно отмечено как выполненное"

    def save(self, *args, **kwargs):
        if self.actual_quantity is not None and self.actual_quantity > 0:
            self.status = self.Status.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            self.status = self.Status.ASSIGNMENT
            self.completed_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.shift_date} {self.get_shift_type_display()} - "
            f"Станок #{self.machine_number} ({self.operator})"
        )

    class Meta:
        verbose_name = _('Сменное задание')
        verbose_name_plural = _('Сменные задания')
        ordering = ['-shift_date', 'shift_type', 'machine_number']
        unique_together = ['shift_date', 'shift_type', 'machine_number']
        indexes = [
            models.Index(fields=['shift_date']),
            models.Index(fields=['status']),
            models.Index(fields=['production_plan']),
        ]


class ShiftAssignmentArchive(models.Model):
    original_id = models.PositiveIntegerField(
        verbose_name=_('ID оригинального задания')
    )
    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_assignments',
        verbose_name=_('План производства')
    )
    shift_date = models.DateField(
        verbose_name=_('Дата смены'),
        default=date.today,
        db_index=True
    )
    shift_type = models.CharField(
        max_length=10,
        choices=ShiftAssignment.ShiftType.choices,
        verbose_name=_('Тип смены'),
        default=ShiftAssignment.ShiftType.DAY
    )
    machine_number = models.CharField(
        max_length=50,
        verbose_name=_('Номер станка'),
        blank=True,
        null=True
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Оператор')
    )
    planned_quantity = models.PositiveIntegerField(
        verbose_name=_('Плановое количество'),
        default=0
    )
    actual_quantity = models.PositiveIntegerField(
        verbose_name=_('Фактическое количество')
    )
    completion_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_('Время выполнения')
    )
    quality_status = models.BooleanField(
        default=False,
        verbose_name=_('Пройдена проверка качества')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )
    archived_at = models.DateTimeField(
        verbose_name=_('Дата архивации'),
        default=timezone.now,
        editable=False
    )

    def __str__(self):
        return f"Архив задания #{self.original_id}"

    @classmethod
    def create_from_assignment(cls, assignment):
        return cls.objects.create(
            original_id=assignment.id,
            production_plan=assignment.production_plan,
            shift_date=assignment.shift_date,
            shift_type=assignment.shift_type,
            machine_number=assignment.machine_number,
            operator=assignment.operator,
            planned_quantity=assignment.planned_quantity,
            actual_quantity=assignment.actual_quantity,
            notes=assignment.notes,
            quality_status=False
        )

    class Meta:
        verbose_name = _('Архивное задание')
        verbose_name_plural = _('Архив заданий')
        ordering = ['-archived_at']
        indexes = [
            models.Index(fields=['original_id']),
            models.Index(fields=['shift_date']),
            models.Index(fields=['operator']),
        ]
