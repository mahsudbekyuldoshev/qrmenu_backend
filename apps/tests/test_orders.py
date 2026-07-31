from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models import Category, Dish, Order, Restaurant, Table, User


class BaseOrderTestCase(APITestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Rest", slug="test-rest")
        self.other_restaurant = Restaurant.objects.create(
            name="Boshqa Rest", slug="boshqa-rest"
        )

        self.manager = User.objects.create_user(
            phone="+998900000001",
            password="password123",
            role=User.Role.MANAGER,
            restaurant=self.restaurant,
        )
        self.waiter = User.objects.create_user(
            phone="+998900000002",
            password="password123",
            role=User.Role.WAITER,
            restaurant=self.restaurant,
        )
        self.chef = User.objects.create_user(
            phone="+998900000003",
            password="password123",
            role=User.Role.CHEF,
            restaurant=self.restaurant,
        )

        self.category = Category.objects.create(
            restaurant=self.restaurant, name="Ichimliklar", slug="ichimliklar"
        )
        self.dish = Dish.objects.create(
            category=self.category, name="Cola", price=10000
        )
        self.table = Table.objects.create(restaurant=self.restaurant, number="1")

        self.list_url = reverse("order-list")


class OrderCreateTests(BaseOrderTestCase):
    """order-list (POST): xodim (waiter odatda) buyurtma yaratadi."""

    def test_requires_authentication(self):
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_waiter_can_create_order(self):
        self.client.force_authenticate(user=self.waiter)
        data = {
            "table": self.table.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": 2}],
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.restaurant_id, self.restaurant.id)  # perform_create orqali
        self.assertEqual(int(order.total_price), 20000)

    def test_restaurant_is_auto_assigned_not_from_payload(self):
        """restaurant maydoni read_only — perform_create orqali user.restaurant'dan olinadi,
        hatto boshqa restoran ID yuborilsa ham e'tiborga olinmasligi kerak."""
        self.client.force_authenticate(user=self.waiter)
        data = {
            "restaurant": self.other_restaurant.id,
            "table": self.table.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": 1}],
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.first()
        self.assertEqual(order.restaurant_id, self.restaurant.id)

    def test_empty_items_rejected(self):
        self.client.force_authenticate(user=self.waiter)
        data = {"table": self.table.id, "uploaded_items": []}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("uploaded_items", response.data)

    def test_invalid_dish_id_rolls_back_order(self):
        """TUZATISH: yaroqsiz dish ID kelsa butun order rollback qilinishi kerak."""
        self.client.force_authenticate(user=self.waiter)
        data = {
            "table": self.table.id,
            "uploaded_items": [{"dish": 999999, "quantity": 1}],
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)  # rollback bo'lgan

    def test_negative_quantity_rejected(self):
        self.client.force_authenticate(user=self.waiter)
        data = {
            "table": self.table.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": -1}],
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_table_from_other_restaurant_rejected(self):
        other_table = Table.objects.create(
            restaurant=self.other_restaurant, number="1"
        )
        self.client.force_authenticate(user=self.waiter)
        data = {
            "table": other_table.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": 1}],
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("table", response.data)

    def test_manager_can_also_create_order(self):
        self.client.force_authenticate(user=self.manager)
        data = {
            "table": self.table.id,
            "uploaded_items": [{"dish": self.dish.id, "quantity": 1}],
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OrderListTests(BaseOrderTestCase):
    """order-list (GET): manager/waiter/chef — barchasi ko'ra oladi (IsRestaurantStaff)."""

    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(
            restaurant=self.restaurant, table=self.table, status=Order.Status.PENDING
        )
        Order.objects.create(restaurant=self.other_restaurant)

    def test_chef_can_list_orders(self):
        """KDS panelida oshpaz buyurtmalarni ko'rishi kerak."""
        self.client.force_authenticate(user=self.chef)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_waiter_can_list_orders(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tenant_isolation(self):
        """Faqat o'z restoraniga tegishli buyurtmalar ko'rinishi kerak."""
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.list_url)
        restaurant_ids = {o["restaurant"] for o in response.data}
        self.assertEqual(restaurant_ids, {self.restaurant.id})

    def test_filter_by_status(self):
        Order.objects.create(
            restaurant=self.restaurant, status=Order.Status.READY
        )
        self.client.force_authenticate(user=self.chef)
        response = self.client.get(self.list_url, {"status": "ready"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(o["status"] == "ready" for o in response.data))

    def test_filter_by_multiple_statuses(self):
        Order.objects.create(restaurant=self.restaurant, status=Order.Status.READY)
        self.client.force_authenticate(user=self.chef)
        response = self.client.get(self.list_url, {"status": "pending,ready"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class OrderUpdateTests(BaseOrderTestCase):
    """order-detail (PATCH): status o'zgartirish - KDS/waiter uchun asosiy oqim."""

    def setUp(self):
        super().setUp()
        self.order = Order.objects.create(
            restaurant=self.restaurant, table=self.table, status=Order.Status.PENDING
        )
        self.detail_url = reverse("order-detail", kwargs={"pk": self.order.id})

    def test_chef_can_update_status_to_preparing(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.patch(
            self.detail_url, {"status": Order.Status.PREPARING}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PREPARING)

    def test_waiter_can_update_status_to_delivered(self):
        self.order.status = Order.Status.READY
        self.order.save()
        self.client.force_authenticate(user=self.waiter)
        response = self.client.patch(
            self.detail_url, {"status": Order.Status.DELIVERED}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_update_order_from_other_restaurant(self):
        other_order = Order.objects.create(
            restaurant=self.other_restaurant, status=Order.Status.PENDING
        )
        other_detail_url = reverse("order-detail", kwargs={"pk": other_order.id})

        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            other_detail_url, {"status": Order.Status.PREPARING}, format="json"
        )
        # get_queryset restaurant bo'yicha filtrlagani uchun 404 qaytishi kerak
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_restaurant_field_is_read_only_on_update(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            self.detail_url,
            {"restaurant": self.other_restaurant.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.restaurant_id, self.restaurant.id)  # o'zgarmagan