from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserRoles

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты модели пользователя"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.operator = User.objects.create_user(
            username='operator1',
            password='testpass123',
            email='operator@example.com',
            first_name='Иван',
            last_name='Петров',
            role=UserRoles.OPERATOR,
            phone='+79991234567'
        )

        self.master = User.objects.create_user(
            username='master1',
            password='masterpass',
            email='master@example.com',
            first_name='Алексей',
            last_name='Сидоров',
            role=UserRoles.MASTER,
            phone='+79997654321'
        )

    def test_создание_пользователя(self):
        """Проверка корректного создания пользователя"""
        print("\n=== Тест 1: Проверка создания пользователя ===")

        # Проверка оператора
        self.assertEqual(self.operator.role, UserRoles.OPERATOR,
                         "Роль оператора должна быть 'operator'")
        self.assertEqual(self.operator.get_role_display(), "Оператор",
                         "Отображаемое название роли должно быть 'Оператор'")
        self.assertEqual(str(self.operator), "Иван Петров (Оператор)",
                         "Строковое представление пользователя неверно")

        # Проверка мастера
        self.assertTrue(self.master.is_master,
                        "Пользователь с ролью MASTER должен возвращать True для is_master")

        print("[✓] Тест создания пользователей пройден успешно")

    def test_проверка_ролей(self):
        """Тестирование функционала ролей"""
        print("\n=== Тест 2: Проверка функционала ролей ===")

        # Создаем администратора для теста
        admin = User.objects.create_user(
            username='admin1',
            password='adminpass',
            first_name='Админ',
            last_name='Админов',
            role=UserRoles.ADMIN
        )

        # Проверяем свойства ролей
        self.assertTrue(self.operator.is_operator,
                        "Опертор должен иметь свойство is_operator=True")
        self.assertFalse(self.operator.is_master,
                         "Опертор не должен быть мастером")
        self.assertTrue(admin.is_admin,
                        "Администратор должен иметь свойство is_admin=True")

        print("[✓] Тест проверки ролей пройден успешно")

    def test_связь_мастер_оператор(self):
        """Тестирование связи между мастером и оператором"""
        print("\n=== Тест 3: Проверка связи мастер-оператор ===")

        # Назначаем оператору мастера
        self.operator.master = self.master
        self.operator.save()

        # Проверяем связь
        self.assertEqual(self.operator.master, self.master,
                         "Оператор должен быть привязан к мастеру")
        self.assertIn(self.operator, self.master.operators.all(),
                      "Мастер должен видеть своего оператора в related_operators")

        print("[✓] Тест связи мастер-оператор пройден успешно")