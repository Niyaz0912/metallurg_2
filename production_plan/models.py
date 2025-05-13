from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class DirectorProductionPlan(models.Model):
    production_plan = models.OneToOneField('production_plan.ProductionPlan', on_delete=models.CASCADE)
    # Дополнительные поля для директора, если нужны
    notes = models.TextField(blank=True, verbose_name=_('Примечания'))

    def __str__(self):
        return str(self.production_plan)


class ProductionPlan(models.Model):
    customer = models.CharField(
        max_length=255,
        verbose_name=_('Заказчик'),
        help_text=_('Название компании-заказчика')
    )
    order_name = models.CharField(
        max_length=255,
        verbose_name=_('Наименование заказа'),
        help_text=_('Наименование производственного заказа'),
        db_index=True,
        null=True,
        blank=True,
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
    deadline = models.DateField(
        verbose_name=_('Срок выполнения'),
        help_text=_('Планируемая дата завершения производства')
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
        return f"{self.order_name} - {self.product} ({self.customer})"

    def clean(self):
        if self.deadline is None:
            raise ValidationError(_("Срок выполнения обязателен для заполнения"))

        if self.deadline < timezone.now().date():
            raise ValidationError(_("Срок выполнения не может быть в прошлом"))

        if self.quantity <= 0:
            raise ValidationError(_("Количество должно быть положительным числом"))

        if not self.order_name.strip():
            raise ValidationError(_("Наименование заказа не может быть пустым"))

        if not self.customer.strip():
            raise ValidationError(_("Заказчик не может быть пустым"))

    class Meta:
        verbose_name = _('Производственный план')
        verbose_name_plural = _('Производственные планы')
        ordering = ['-deadline']
        indexes = [
            models.Index(fields=['order_name']),
            models.Index(fields=['customer']),
            models.Index(fields=['deadline']),
        ]

