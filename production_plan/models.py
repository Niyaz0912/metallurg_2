from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator


class DirectorProductionPlan(models.Model):
    production_plan = models.OneToOneField('production_plan.ProductionPlan', on_delete=models.CASCADE)
    # Дополнительные поля для директора, если нужны
    notes = models.TextField(blank=True, verbose_name=_('Примечания'))

    def __str__(self):
        return str(self.production_plan)


class ProductionPlan(models.Model):
    customer = models.CharField(
        max_length=255,
        verbose_name='Заказчик',
        validators=[MinLengthValidator(1)],
    )
    order_name = models.CharField(
        max_length=255,
        verbose_name='Наименование заказа',
        db_index=True,
        default='Без названия',  # Добавлено значение по умолчанию
        help_text='Наименование производственного заказа'
    )
    product = models.CharField(max_length=255, verbose_name='Изделие')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    drawing_number = models.CharField(max_length=100, blank=True, verbose_name='Чертеж')
    deadline = models.DateField(verbose_name='Срок выполнения')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'Производственный план'
        verbose_name_plural = 'Производственные планы'
        ordering = ['-deadline']
        indexes = [
            models.Index(fields=['order_name']),
            models.Index(fields=['customer']),
            models.Index(fields=['deadline']),
        ]

    @property
    def completed_quantity(self):
        from shift_assignment.models import ShiftAssignment
        return self.shift_assignments.filter(
            status=ShiftAssignment.Status.COMPLETED
        ).aggregate(total=Sum('actual_quantity'))['total'] or 0

    @property
    def progress(self):
        if self.quantity > 0:
            return round((self.completed_quantity / self.quantity) * 100, 1)
        return 0

    @property
    def is_overdue(self):
        return timezone.now().date() > self.deadline

    def __str__(self):
        return f"{self.order_name} - {self.product} ({self.customer})"

    def clean(self):
        if not self.deadline:
            raise ValidationError("Срок выполнения обязателен для заполнения")
        if self.deadline < timezone.now().date():
            raise ValidationError("Срок выполнения не может быть в прошлом")
        if self.quantity <= 0:
            raise ValidationError("Количество должно быть положительным числом")
        if not self.order_name.strip():
            raise ValidationError("Наименование заказа не может быть пустым")
        if not self.customer.strip():
            raise ValidationError("Заказчик не может быть пустым")
