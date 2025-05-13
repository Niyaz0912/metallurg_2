import os
import django

# Укажите путь к вашим настройкам Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализация Django
django.setup()

from django_tables2 import SingleTableView

print("Импорт прошёл успешно!")
