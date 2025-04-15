from django.db import models
from django.conf import settings


class ShiftAssignment(models.Model):
    customer = models.CharField(max_length=255)
    date = models.DateField()
    machine_number = models.IntegerField()
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shifts')
    order = models.CharField(max_length=255)
    part = models.CharField(max_length=255)
    quantity = models.IntegerField()
    part_blueprint = models.FileField(upload_to='part_blueprints/')
    execution_status = models.BooleanField(default=False)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f'Сменное задание для {self.operator.username}'

    class Meta:
        verbose_name = 'Shift Assignment'
        verbose_name_plural = 'Shift Assignments'
