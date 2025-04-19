from django.contrib import admin
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели User.

    Этот класс определяет, какие поля будут отображаться в списке
    объектов модели User в административной панели, а также
    предоставляет возможность поиска и фильтрации.
    """

    # Поля, которые будут отображаться в списке объектов
    list_display = ('username', 'last_name', 'first_name', 'role', 'pk', 'is_active')

    # Поля, по которым можно фильтровать список объектов
    list_filter = ('last_name', 'is_active')

    # Поля, по которым можно осуществлять поиск
    search_fields = ('username', 'last_name', 'first_name')

    # Сортировка списка объектов по фамилии и имени
    ordering = ('last_name', 'first_name')