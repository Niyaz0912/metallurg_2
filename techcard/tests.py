from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from production_plan.models import ProductionPlan
from .models import TechCard

User = get_user_model()

class TechCardBasicTests(TestCase):
    def setUp(self):
        # Создаём пользователя-директора
        self.director = User.objects.create_user(
            username='director',
            password='pass1234',
            role='director'
        )
        # Обычный пользователь
        self.user = User.objects.create_user(
            username='user',
            password='pass1234',
            role='operator'
        )
        # Создаём ProductionPlan для связи с TechCard
        self.production_plan = ProductionPlan.objects.create(
            customer='Test Customer',
            order_name='Test Order',
            product='Test Product',
            quantity=100,
            deadline='2099-12-31'  # дата в будущем
        )
        # Создаём TechCard с обязательными полями
        self.techcard = TechCard.objects.create(
            production_plan=self.production_plan,
            total_quantity=100,
            technological_process='Тестовый технологический маршрут'
        )

    def test_techcard_creation(self):
        print("\n=== Тест: Создание техкарты ===")
        self.assertEqual(self.techcard.production_plan, self.production_plan)
        self.assertEqual(self.techcard.total_quantity, 100)
        print("[✓] Тест создания техкарты пройден успешно")

    def test_list_view_access_for_director(self):
        print("\n=== Тест: Доступ к списку техкарт для директора ===")
        self.client.force_login(self.director)
        url = reverse('techcard:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.production_plan.product)
        print("[✓] Тест доступа к списку техкарт для директора пройден успешно")

    def test_list_view_access_for_non_director(self):
        print("\n=== Тест: Запрет доступа к списку техкарт для не-директора ===")
        self.client.force_login(self.user)
        url = reverse('techcard:list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [403, 404])
        print("[✓] Тест запрета доступа к списку техкарт для не-директора пройден успешно")

    def test_detail_view_access_for_logged_in_user(self):
        print("\n=== Тест: Доступ к детальному просмотру техкарты для авторизованного пользователя ===")
        self.client.force_login(self.user)
        url = reverse('techcard:detail', args=[self.techcard.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.production_plan.customer)
        print("[✓] Тест доступа к детальному просмотру техкарты пройден успешно")

    def test_create_view_access_for_director(self):
        print("\n=== Тест: Доступ к созданию техкарты для директора ===")
        self.client.force_login(self.director)
        url = reverse('techcard:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        print("[✓] Тест доступа к созданию техкарты для директора пройден успешно")
