from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ProductionPlan(models.Model):
    """
    Модель производственного плана.
    Содержит информацию о заказах клиентов и планах производства.
    """
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
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_plans',
        verbose_name=_('Автор плана'),
        help_text=_('Пользователь, создавший план')
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
        """Валидация данных перед сохранением"""
        if self.deadline is None:
            raise ValidationError(_("Срок выполнения обязателен для заполнения"))

        if self.deadline < timezone.now().date():
            raise ValidationError(_("Срок выполнения не может быть в прошлом"))

        if self.quantity <= 0:
            raise ValidationError(_("Количество должно быть положительным числом"))

        if not 0 <= self.progress <= 100:
            raise ValidationError(_("Прогресс должен быть в диапазоне 0-100%"))

    def save(self, *args, **kwargs):
        """Автоматическое обновление статуса завершения"""
        self.is_completed = self.progress >= 100
        self.full_clean()
        super().save(*args, **kwargs)

    def update_progress(self):
        """Обновляет процент выполнения на основе выполненных заданий"""
        from shift_assignment.models import ShiftAssignment
        completed_qty = ShiftAssignment.objects.filter(
            production_plan=self,
            execution_status=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

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
        ]


class Supply(models.Model):
    """
    Модель поставки материалов и комплектующих для производственного плана.
    """
    STATUS_CHOICES = [
        ('pending', _('Ожидается')),
        ('delivered', _('Доставлено')),
        ('canceled', _('Отменено')),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name=_('Наименование'),
        help_text=_('Название материала или комплектующего')
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_('Количество'),
        help_text=_('Количество поставляемых единиц')
    )
    expected_date = models.DateField(
        verbose_name=_('Ожидаемая дата'),
        help_text=_('Планируемая дата поставки')
    )
    received_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Фактическая дата'),
        help_text=_('Дата фактического получения')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус поставки'),
        db_index=True
    )
    production_plan = models.ForeignKey(
        ProductionPlan,
        on_delete=models.CASCADE,
        related_name='supplies',
        verbose_name=_('Производственный план'),
        help_text=_('Связанный производственный план')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания'),
        help_text=_('Дополнительная информация о поставке')
    )
    created_at = models.DateTimeField(
        default=timezone.now,  # Изменено с auto_now_add на default
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def clean(self):
        """Валидация данных поставки"""
        if self.received_date and self.received_date > timezone.now().date():
            raise ValidationError(_("Дата получения не может быть в будущем"))
        if self.received_date and not self.expected_date:
            raise ValidationError(_("Укажите ожидаемую дату поставки"))

    def save(self, *args, **kwargs):
        """Автоматическое обновление статуса при получении"""
        if self.received_date and self.status == 'pending':
            self.status = 'delivered'
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Поставка')
        verbose_name_plural = _('Поставки')
        ordering = ['-expected_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expected_date']),
            models.Index(fields=['production_plan']),
        ]