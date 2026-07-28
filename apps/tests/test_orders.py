from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models.orders import Order
from apps.models.restaurants import Category, Dish, Restaurant


class OrderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@test.com", password="password"
        )
        self.restaurant = Restaurant.objects.create(
            name="Test Rest", slug="test-rest", owner=self.user
        )
        self.category = Category.objects.create(
            restaurant=self.restaurant, name="Drinks", slug="drinks"
        )
        self.dish = Dish.objects.create(
            category=self.category, name="Cola", price=10000
        )

        self.order_url = reverse("order-list")

    def test_create_order(self):
        data = {
            "restaurant": self.restaurant.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": 2}],
        }
        response = self.client.post(self.order_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_price, 20000)

    def test_update_order_status(self):
        order = Order.objects.create(
            restaurant=self.restaurant, status=Order.Status.PENDING
        )
        update_url = reverse("order-detail", kwargs={"pk": order.id})
        data = {"status": Order.Status.PREPARING}

        response = self.client.patch(update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
