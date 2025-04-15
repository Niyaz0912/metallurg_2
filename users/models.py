from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRoles(models.TextChoices):
    """
    Определение ролей пользователей с использованием TextChoices.

    Это перечисление содержит доступные роли пользователей в системе:
    - Оператор
    - Мастер
    - Администратор
    """
    EMPLOYEE = 'employee', _('Employee')
    OPERATOR = 'operator', _('Operator')
    MASTER = 'master', _('Master')
    DIRECTOR = 'director', _('Director')
    ADMIN = 'admin', _('Administrator')


class User(AbstractUser):
    surname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, choices=UserRoles.choices)
    phone = models.CharField(max_length=20, blank=True, null=True)

    USERNAME_FIELD = 'username'  # Используйте стандартное поле для входа
    REQUIRED_FIELDS = ['surname', 'name', 'role', 'phone']

    def __str__(self):
        """Возвращает строковое представление объекта пользователя."""
        return f'{self.name} {self.surname}'

    class Meta:
        """Метаданные модели."""
        verbose_name = 'User'  # Человекочитаемое имя в единственном числе
        verbose_name_plural = 'Users'  # Человекочитаемое имя во множественном числе
        ordering = ['username']  # Сортировка по username по умолчанию
