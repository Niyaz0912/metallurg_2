from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ProductionPlan(models.Model):
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    order = models.CharField(max_length=255, verbose_name='Заказ')
    product = models.CharField(max_length=255, verbose_name='Продукция')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    plan = models.FileField(upload_to='production_plans/', verbose_name='План производства')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_plans',
        verbose_name='Создано'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_plans',
        null=True,
        blank=True,
        verbose_name='Обновлено'
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Процент выполнения',
        help_text='0-100%'
    )
    is_completed = models.BooleanField(default=False, verbose_name='Завершён')
    deadline = models.DateField(verbose_name='Срок отгрузки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'Заказ {self.order} ({self.customer})'

    def save(self, *args, **kwargs):
        self.is_completed = self.progress >= 100
        super().save(*args, **kwargs)

    def update_progress(self):
        """Обновляет процент выполнения на основе связанных сменных заданий"""
        from shift_assignment.models import ShiftAssignment
        completed_qty = ShiftAssignment.objects.filter(
            order=self.order,
            execution_status=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        self.progress = min(100, int((completed_qty / self.quantity) * 100))
        self.save()

    class Meta:
        verbose_name = _('План производства')
        verbose_name_plural = _('Планы производства')
        ordering = ['-deadline']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['customer']),
            models.Index(fields=['deadline']),
        ]


class Supply(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Ожидается'),
        ('received', 'Получена'),
        ('canceled', 'Отменена'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    expected_date = models.DateField(verbose_name='Ожидаемая дата')
    received_date = models.DateField(null=True, blank=True, verbose_name='Дата получения')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='upcoming',
        verbose_name='Статус'
    )
    production_plan = models.ForeignKey(
        ProductionPlan,
        on_delete=models.CASCADE,
        related_name='supplies',
        verbose_name='План производства',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    class Meta:
        verbose_name = _('Поставка')
        verbose_name_plural = _('Поставки')
        ordering = ['-expected_date']
