from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'master')
    list_filter = ('role', 'master')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Work info'), {'fields': ('role', 'master')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
