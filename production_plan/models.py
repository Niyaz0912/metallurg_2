from django.db import models
from django.conf import settings


class ProductionPlan(models.Model):
    customer = models.CharField(max_length=255)
    order = models.CharField(max_length=255)
    product = models.CharField(max_length=255)
    quantity = models.IntegerField()
    plan = models.FileField(upload_to='production_plans/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_plans')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='updated_plans', null=True, blank=True)
    progress = models.IntegerField(default=0)  # Процент выполнения
    deadline = models.DateTimeField()  # Срок отгрузки

    def __str__(self):
        return f'Заказ {self.order} для {self.customer}'

    class Meta:
        verbose_name = 'Production Plan'
        verbose_name_plural = 'Production Plans'
