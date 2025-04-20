from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRoles(models.TextChoices):
    """
    Определение ролей пользователей с использованием TextChoices.

    Это перечисление содержит доступные роли пользователей в системе:
    - Сотрудник
    - Оператор
    - Мастер
    - Директор
    - Администратор
    """
    EMPLOYEE = 'employee', _('Employee')
    OPERATOR = 'operator', _('Operator')
    MASTER = 'master', _('Master')
    DIRECTOR = 'director', _('Director')
    ADMIN = 'admin', _('Administrator')


class User(AbstractUser):
    role = models.CharField(
        max_length=255,
        choices=UserRoles.choices,
        verbose_name=_('Role')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone')
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role', 'phone']

    def __str__(self):
        """Возвращает строковое представление объекта пользователя."""
        return f'{self.get_full_name()}'

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
