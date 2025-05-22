from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from production_plan.models import ProductionPlan
from .models import ShiftAssignment
from users.models import User


class ShiftAssignmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_operator", role='operator')
        self.plan = ProductionPlan.objects.create(
            customer="Металлург",
            product="Звезда",
            quantity=100,
            deadline=timezone.now().date() + timedelta(days=7)
        )
        self.assignment = ShiftAssignment.objects.create(
            production_plan=self.plan,
            shift_date=timezone.now(),
            shift_type=ShiftAssignment.ShiftType.DAY,
            operator=self.user,
            planned_quantity=50
        )

    def test_complete_assignment(self):
        print("\n=== Тест: Завершение сменного задания ===")
        result, message = self.assignment.complete(actual_quantity=50, user=self.user)
        self.assertTrue(result)
        self.assertEqual(message, "Задание успешно завершено")
        self.assertEqual(self.assignment.status, ShiftAssignment.Status.COMPLETED)
        self.assertIsNotNone(self.assignment.completed_at)
        print("[✓] Тест завершения сменного задания пройден успешно")


class AccessControlTests(TestCase):
    def setUp(self):
        self.master = User.objects.create(username="test_master", role='master')
        self.operator = User.objects.create(username="test_operator", role='operator')
        self.plan = ProductionPlan.objects.create(
            customer="Металлург",
            product="Звезда",
            quantity=100,
            deadline=timezone.now().date() + timedelta(days=7)
        )
        self.assignment = ShiftAssignment.objects.create(
            production_plan=self.plan,
            operator=self.operator
        )
        self.client = Client()

    def test_access_for_master(self):
        print("\n=== Тест: Доступ мастера к активным сменным заданиям ===")
        self.client.force_login(self.master)
        url = reverse('shift_assignment:active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Активные задания")
        self.assertContains(response, str(self.assignment.id))  # Проверяем, что ID задания есть на странице
        print("[✓] Тест доступа мастера пройден успешно")

    def test_access_for_operator(self):
        print("\n=== Тест: Доступ оператора к активным сменным заданиям ===")
        self.client.force_login(self.operator)
        url = reverse('shift_assignment:active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Активные задания")
        self.assertContains(response, self.operator.username)
        print("[✓] Тест доступа оператора пройден успешно")
