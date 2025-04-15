from django.core.management import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Создаёт стандартных пользователей: admin, director, master, operator, employee"

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'admin@company.com',
                'email': 'admin@company.com',
                'first_name': 'Администратор',
                'last_name': 'Системный',
                'password': os.getenv('ADMIN_PASSWORD', 'admin123'),
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            },
            {
                'username': 'director@company.com',
                'email': 'director@company.com',
                'first_name': 'Директор',
                'last_name': 'Главный',
                'password': os.getenv('DIRECTOR_PASSWORD', 'director123'),
                'role': 'director',
                'is_staff': True,
                'is_superuser': False,
                'is_active': True
            },
            {
                'username': 'master@company.com',
                'email': 'master@company.com',
                'first_name': 'Мастер',
                'last_name': 'Управляющий',
                'password': os.getenv('MASTER_PASSWORD', 'master123'),
                'role': 'master',
                'is_staff': True,
                'is_superuser': False,
                'is_active': True
            },
            {
                'username': 'operator@company.com',
                'email': 'operator@company.com',
                'first_name': 'Оператор',
                'last_name': 'Сменный',
                'password': os.getenv('OPERATOR_PASSWORD', 'operator123'),
                'role': 'operator',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True
            },
            {
                'username': 'employee@company.com',
                'email': 'employee@company.com',
                'first_name': 'Сотрудник',
                'last_name': 'Обычный',
                'password': os.getenv('EMPLOYEE_PASSWORD', 'employee123'),
                'role': 'employee',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True
            }
        ]

        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    is_staff=user_data['is_staff'],
                    is_superuser=user_data['is_superuser'],
                    is_active=user_data['is_active']
                )
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user_data["username"]} ({user_data["role"]})'))
            else:
                self.stdout.write(self.style.WARNING(f'Пользователь {user_data["username"]} уже существует'))
