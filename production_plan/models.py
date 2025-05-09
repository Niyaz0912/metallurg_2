from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ProductionPlan(models.Model):
    customer = models.CharField(
        max_length=255,
        verbose_name=_('Заказчик'),
        help_text=_('Название компании-заказчика')
    )
    order = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Номер заказа'),
        help_text=_('Уникальный идентификатор заказа'),
        db_index=True
    )
    product = models.CharField(
        max_length=255,
        verbose_name=_('Изделие'),
        help_text=_('Наименование производимого изделия')
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_('Количество'),
        help_text=_('Общее количество изделий для производства')
    )
    drawing_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Чертеж/Модель'),
        help_text=_('Номер чертежа или модели изделия')
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Процент выполнения'),
        help_text=_('0-100%')
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Завершён'),
        help_text=_('Отметьте, если план выполнен полностью')
    )
    deadline = models.DateField(
        verbose_name=_('Срок выполнения'),
        help_text=_('Планируемая дата завершения производства')
    )

    STATUS_CHOICES = [
        ('planned', _('Запланировано')),
        ('in_progress', _('В работе')),
        ('completed', _('Выполнено')),
        ('cancelled', _('Отменено')),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name=_('Статус'),
        help_text=_('Статус выполнения плана'),
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления'),
        db_index=True
    )

    def __str__(self):
        return f"{self.order} - {self.product} ({self.customer})"

    def clean(self):
        if self.deadline is None:
            raise ValidationError(_("Срок выполнения обязателен для заполнения"))

        if self.deadline < timezone.now().date():
            raise ValidationError(_("Срок выполнения не может быть в прошлом"))

        if self.quantity <= 0:
            raise ValidationError(_("Количество должно быть положительным числом"))

        if not 0 <= self.progress <= 100:
            raise ValidationError(_("Прогресс должен быть в диапазоне 0-100%"))

        if not self.order.strip():
            raise ValidationError(_("Номер заказа не может быть пустым"))

        if not self.customer.strip():
            raise ValidationError(_("Заказчик не может быть пустым"))

    def save(self, *args, **kwargs):
        self.is_completed = self.progress >= 100
        self.full_clean()
        super().save(*args, **kwargs)

    def update_progress(self):
        from shift_assignment.models import ShiftAssignment
        completed_qty = ShiftAssignment.objects.filter(
            production_plan=self,
            status=ShiftAssignment.Status.COMPLETED
        ).aggregate(total=models.Sum('actual_quantity'))['total'] or 0

        if self.quantity == 0:
            self.progress = 0
        else:
            self.progress = min(100, int((completed_qty / self.quantity) * 100))

        self.save()

    class Meta:
        verbose_name = _('Производственный план')
        verbose_name_plural = _('Производственные планы')
        ordering = ['-deadline']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['customer']),
            models.Index(fields=['deadline']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['status']),
        ]
