from django.test import TestCase
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import User
from .models import ProductionPlan


class ProductionPlanModelTests(TestCase):
    """Тесты модели ProductionPlan"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            first_name='Ivan',
            last_name='Petrov',
            role='master',
            password='testpass123'
        )

        self.valid_data = {
            'customer': "Test Client",
            'order_name': "Test Order",
            'product': "Test Product",
            'quantity': 100,
            'deadline': timezone.now().date() + timedelta(days=7)
        }

    def test_plan_creation(self):
        plan = ProductionPlan.objects.create(**self.valid_data)
        self.assertEqual(plan.product, "Test Product")
        self.assertEqual(plan.quantity, 100)
        self.assertGreaterEqual(plan.deadline, timezone.now().date())
        print("\n=== Тест: Создание производственного плана ===")
        print("[✓] Тест создания производственного плана пройден успешно")

    def test_invalid_deadline_validation(self):
        print("\n=== Тест: Валидация просроченного срока ===")
        invalid_data = self.valid_data.copy()
        invalid_data['deadline'] = timezone.now().date() - timedelta(days=1)

        plan = ProductionPlan(**invalid_data)
        with self.assertRaises(ValidationError):
            plan.full_clean()
        print("[✓] Тест валидации просроченного срока пройден успешно")

    def test_blank_customer_validation(self):
        print("\n=== Тест: Валидация пустого заказчика ===")
        invalid_data = self.valid_data.copy()
        invalid_data['customer'] = '   '

        plan = ProductionPlan(**invalid_data)
        with self.assertRaises(ValidationError):
            plan.full_clean()
        print("[✓] Тест валидации пустого заказчика пройден успешно")


class ProductionPlanViewTests(TestCase):
    """Тесты представлений ProductionPlan"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2',
            first_name='Alexey',
            last_name='Sidorov',
            role='operator',
            password='testpass123'
        )

        self.plan = ProductionPlan.objects.create(
            customer="Second Client",
            order_name="Order 2",
            product="Another Product",
            quantity=50,
            deadline=timezone.now().date() + timedelta(days=14)
        )

    def test_plan_list_access(self):
        print("\n=== Тест: Доступ к списку производственных планов ===")
        self.client.force_login(self.user)
        url = reverse('production_plan:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.product)
        print("[✓] Тест доступа к списку производственных планов пройден успешно")

    def test_plan_detail_access(self):
        print("\n=== Тест: Доступ к детальному просмотру плана ===")
        self.client.force_login(self.user)
        url = reverse('production_plan:detail', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.customer)
        print("[✓] Тест доступа к детальному просмотру плана пройден успешно")
