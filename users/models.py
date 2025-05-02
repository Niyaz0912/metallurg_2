from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRoles(models.TextChoices):
    """Роли пользователей в системе"""
    EMPLOYEE = 'employee', _('Сотрудник')
    OPERATOR = 'operator', _('Оператор')
    MASTER = 'master', _('Мастер')
    DIRECTOR = 'director', _('Директор')
    ADMIN = 'admin', _('Администратор')


class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    role = models.CharField(
        max_length=255,
        choices=UserRoles.choices,
        default=UserRoles.OPERATOR,
        verbose_name=_('Роль')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Телефон')
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role', 'phone']

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    def get_role_display(self):
        return dict(UserRoles.choices)[self.role]

    @property
    def is_master(self):
        return self.role == 'master'  # Исправлено: прямое сравнение со строкой

    @property
    def is_operator(self):
        return self.role == 'operator'  # Исправлено: прямое сравнение со строкой

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['last_name', 'first_name']