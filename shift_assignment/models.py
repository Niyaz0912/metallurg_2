from django.db import models
from django.conf import settings
from django.utils import timezone


class ShiftAssignment(models.Model):
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    date = models.DateField(verbose_name='Дата')
    machine_number = models.IntegerField(verbose_name='Номер станка')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name='Оператор'
    )
    part_blueprint = models.FileField(
        upload_to='part_blueprints/',
        verbose_name='Чертеж детали',
        blank=True,
        null=True
    )
    execution_status = models.BooleanField(
        default=False,
        verbose_name='Статус выполнения'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    quantity = models.IntegerField()

    def __str__(self):
        return f'Сменное задание #{self.id} для {self.operator.username}'

    def complete_shift(self):
        """Метод для завершения смены и переноса в архив"""
        if not self.execution_status:
            self.execution_status = True
            self.save()
            ShiftAssignmentArchive.objects.create_from_assignment(self)
        return self.execution_status

    class Meta:
        verbose_name = 'Сменное задание'
        verbose_name_plural = 'Сменные задания'
        ordering = ['-date', 'machine_number']


class ShiftAssignmentArchive(models.Model):
    original_id = models.PositiveIntegerField(verbose_name='ID оригинального задания')
    customer = models.CharField(max_length=255, verbose_name='Клиент')
    date = models.DateField(verbose_name='Дата выполнения')
    machine_number = models.IntegerField(verbose_name='Номер станка')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archived_shifts',
        verbose_name='Оператор'
    )
    order = models.CharField(max_length=255, verbose_name='Заказ')
    part = models.CharField(max_length=255, verbose_name='Деталь')
    quantity = models.IntegerField(verbose_name='Количество')
    part_blueprint = models.FileField(
        upload_to='archived_blueprints/',
        verbose_name='Чертеж детали',
        blank=True,
        null=True
    )
    actual_quantity = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Фактическое количество'
    )
    completed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата завершения'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    quality_check = models.BooleanField(
        default=False,
        verbose_name='Проверка качества'
    )
    shift_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Длительность смены'
    )

    def __str__(self):
        return f'Архивная смена #{self.id} (ориг. #{self.original_id})'

    @classmethod
    def create_from_assignment(cls, assignment):
        """Создает архивную запись на основе выполненного задания"""
        return cls.objects.create(
            original_id=assignment.id,
            customer=assignment.customer,
            date=assignment.date,
            machine_number=assignment.machine_number,
            operator=assignment.operator,
            order=getattr(assignment, 'order', ''),  # если поле есть
            part=getattr(assignment, 'part', ''),    # если поле есть
            quantity=assignment.quantity,
            part_blueprint=assignment.part_blueprint,
            comment=assignment.comment,
            completed_at=timezone.now()
        )

    class Meta:
        verbose_name = 'Архивная смена'
        verbose_name_plural = 'Архив смен'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['original_id']),
            models.Index(fields=['date']),
            models.Index(fields=['operator']),
        ]


class MachineStatus(models.Model):
    STATUS_CHOICES = [
        ('working', 'Работает'),
        ('idle', 'В простое'),
        ('setup', 'На переналадке'),
        ('repair', 'В ремонте'),
    ]

    machine_number = models.IntegerField(verbose_name='Номер станка', unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус станка')
    breakdown_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата и время поломки',
        help_text='Указывайте дату и время, когда станок сломался, если статус "В ремонте"'
    )
    notes = models.TextField(blank=True, verbose_name='Дополнительные заметки')

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления статуса')

    def __str__(self):
        return f'Станок #{self.machine_number} — {self.get_status_display()}'

    class Meta:
        verbose_name = 'Статус станка'
        verbose_name_plural = 'Статусы станков'
        ordering = ['machine_number']
