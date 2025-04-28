from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ShiftAssignment(models.Model):
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    date = models.DateField(verbose_name='Дата задания', default=timezone.now)
    machine_number = models.PositiveIntegerField(verbose_name='Номер станка')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='shift_assignments',
        verbose_name='Оператор'
    )
    part_blueprint = models.FileField(
        upload_to='part_blueprints/',
        verbose_name='Чертеж',
        blank=True,
        null=True
    )
    execution_status = models.BooleanField(default=False, verbose_name='Выполнено')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    order = models.CharField(max_length=255, verbose_name='Номер заказа')
    part = models.CharField(max_length=255, verbose_name='Деталь')
    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_assignments',
        verbose_name='План производства'
    )

    def __str__(self):
        return f'Задание #{self.id} ({self.date})'

    def complete(self):
        """Отмечает задание как выполненное"""
        if not self.execution_status:
            self.execution_status = True
            self.save()
            ShiftAssignmentArchive.create_from_assignment(self)
            if self.production_plan:
                self.production_plan.update_progress()

    class Meta:
        verbose_name = _('Сменное задание')
        verbose_name_plural = _('Сменные задания')
        ordering = ['-date', 'machine_number']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['execution_status']),
            models.Index(fields=['operator']),
        ]


class ShiftAssignmentArchive(models.Model):
    original_id = models.PositiveIntegerField(verbose_name='ID задания')
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    date = models.DateField(verbose_name='Дата выполнения')
    machine_number = models.PositiveIntegerField(verbose_name='Станок')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archived_assignments',
        verbose_name='Оператор'
    )
    order = models.CharField(max_length=255, verbose_name='Заказ')
    part = models.CharField(max_length=255, verbose_name='Деталь')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    actual_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Фактическое количество'
    )
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name='Завершено')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    quality_check = models.BooleanField(default=False, verbose_name='Проверка качества')
    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_assignments',
        verbose_name='План производства'
    )

    @classmethod
    def create_from_assignment(cls, assignment):
        return cls.objects.create(
            original_id=assignment.id,
            customer=assignment.customer,
            date=assignment.date,
            machine_number=assignment.machine_number,
            operator=assignment.operator,
            order=assignment.order,
            part=assignment.part,
            quantity=assignment.quantity,
            actual_quantity=assignment.quantity,
            comment=assignment.comment,
            production_plan=assignment.production_plan
        )

    class Meta:
        verbose_name = _('Архивное задание')
        verbose_name_plural = _('Архив заданий')
        ordering = ['-completed_at']
