from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ProductionPlan(models.Model):
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    order = models.CharField(max_length=255, verbose_name='Заказ')
    product = models.CharField(max_length=255, verbose_name='Продукция')
    quantity = models.IntegerField(verbose_name='Количество')
    plan = models.FileField(upload_to='production_plans/', verbose_name='План производства')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_plans',
        verbose_name='Создано пользователем'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='updated_plans',
        null=True,
        blank=True,
        verbose_name='Обновлено пользователем'
    )
    progress = models.IntegerField(default=0, verbose_name='Процент выполнения')  # Процент выполнения
    is_completed = models.BooleanField(default=False, verbose_name='Завершён')
    deadline = models.DateTimeField(verbose_name='Срок отгрузки')  # Срок отгрузки

    def __str__(self):
        return f'Заказ {self.order} для {self.customer}'

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем is_completed в True, если progress 100% и наоборот
        self.is_completed = self.progress >= 100
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('План производства')
        verbose_name_plural = _('Планы производства')


class Supply(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Ожидается'),
        ('received', 'Получена'),
        ('canceled', 'Отменена'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название поставки')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    expected_date = models.DateField(verbose_name='Ожидаемая дата поставки')
    received_date = models.DateField(null=True, blank=True, verbose_name='Дата получения')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')

    def __str__(self):
        return f"{self.name} — {self.get_status_display()}"

    class Meta:
        verbose_name = _('Поставка')
        verbose_name_plural = _('Поставки')
        ordering = ['-expected_date']
