from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class ShiftAssignment(models.Model):
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    date = models.DateField(verbose_name='Дата задания', default=timezone.now)
    machine_number = models.PositiveIntegerField(verbose_name='Номер станка')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='shift_assignments',
        verbose_name='Оператор',
        to_field='username'
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
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата выполнения')

    def __str__(self):
        return f'Задание #{self.id} ({self.date})'

    @property
    def status_display(self):
        return "Выполнено" if self.execution_status else "В работе"

    def complete(self, user):
        """
        Отмечает задание как выполненное
        Args:
            user: Пользователь, выполняющий операцию

        Returns:
            tuple: (success: bool, message: str)
        """
        # Проверяем, что пользователь - оператор этого задания
        if user.role != 'operator' or user.username != self.operator.username:
            return False, "У вас нет прав для выполнения этого действия"

        # Проверяем, что задание еще не выполнено
        if self.execution_status:
            return False, "Задание уже было выполнено ранее"

        try:
            # Обновляем статус задания
            self.execution_status = True
            self.completed_at = timezone.now()
            self.save()

            # Создаем архивную запись
            ShiftAssignmentArchive.create_from_assignment(self)

            # Обновляем прогресс производственного плана (если есть)
            if self.production_plan:
                self.production_plan.update_progress()

            return True, "Задание успешно отмечено как выполненное"
        except Exception as e:
            logger.error(f"Ошибка при выполнении задания {self.id}: {str(e)}")
            return False, "Произошла ошибка при обновлении задания"

    class Meta:
        verbose_name = _('Сменное задание')
        verbose_name_plural = _('Сменные задания')
        ordering = ['-date', 'machine_number']


class ShiftAssignmentArchive(models.Model):
    """
    Модель для хранения выполненных сменных заданий
    """
    original_id = models.PositiveIntegerField(
        verbose_name='ID оригинального задания',
        help_text='ID задания из основной таблицы'
    )
    customer = models.CharField(
        max_length=255,
        verbose_name='Клиент'
    )
    date = models.DateField(
        verbose_name='Дата выполнения задания'
    )
    machine_number = models.PositiveIntegerField(
        verbose_name='Номер станка'
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_assignments',
        verbose_name='Оператор',
        to_field='username',
        help_text='Пользователь, выполнивший задание'
    )
    order = models.CharField(
        max_length=255,
        verbose_name='Номер заказа'
    )
    part = models.CharField(
        max_length=255,
        verbose_name='Деталь'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Плановое количество'
    )
    actual_quantity = models.PositiveIntegerField(
        verbose_name='Фактическое количество',
        null=True,
        blank=True,
        help_text='Фактически произведенное количество'
    )
    completed_at = models.DateTimeField(
        verbose_name='Дата и время завершения',
        auto_now_add=True
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
        null=True
    )
    quality_check = models.BooleanField(
        verbose_name='Проверка качества',
        default=False,
        help_text='Отметка о прохождении контроля качества'
    )
    production_plan = models.ForeignKey(
        'production_plan.ProductionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_assignments',
        verbose_name='Связанный план производства'
    )

    def __str__(self):
        return f"Архив задания #{self.original_id} ({self.date})"

    @classmethod
    def create_from_assignment(cls, assignment):
        """
        Создает архивную запись на основе сменного задания
        Args:
            assignment (ShiftAssignment): Объект задания для архивирования
        Returns:
            ShiftAssignmentArchive: Созданная архивная запись
        """
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
            production_plan=assignment.production_plan,
            quality_check=False  # По умолчанию проверка качества не пройдена
        )

    @property
    def quality_status(self):
        """Возвращает текстовое представление статуса проверки качества"""
        return "Пройдена" if self.quality_check else "Не пройдена"

    class Meta:
        verbose_name = _('Архивное задание')
        verbose_name_plural = _('Архив заданий')
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['original_id']),
            models.Index(fields=['operator']),
            models.Index(fields=['completed_at']),
        ]