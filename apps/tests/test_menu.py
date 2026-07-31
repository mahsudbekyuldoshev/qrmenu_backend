from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models import Category, Dish, Order, Restaurant, Table


class BaseMenuTestCase(APITestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Rayhon", slug="rayhon", menu_background="backgrounds/test.jpg"
        )
        self.table = Table.objects.create(restaurant=self.restaurant, number="5")

        self.active_category = Category.objects.create(
            restaurant=self.restaurant, name="Salatlar", slug="salatlar", is_active=True
        )
        self.inactive_category = Category.objects.create(
            restaurant=self.restaurant,
            name="Yashirin",
            slug="yashirin",
            is_active=False,
        )

        self.available_dish = Dish.objects.create(
            category=self.active_category,
            name="Sezar salati",
            price=45000,
            is_available=True,
        )
        self.unavailable_dish = Dish.objects.create(
            category=self.active_category,
            name="Tugagan taom",
            price=30000,
            is_available=False,
        )


class PublicMenuViewTests(BaseMenuTestCase):
    """public-menu: auth talab qilmaydi, faqat qr_hash orqali."""

    def setUp(self):
        super().setUp()
        self.url = reverse("public-menu", kwargs={"qr_hash": self.table.qr_hash})

    def test_no_authentication_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_qr_hash_returns_404(self):
        url = reverse("public-menu", kwargs={"qr_hash": "nonexistent-hash"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_table_returns_404(self):
        inactive_table = Table.objects.create(
            restaurant=self.restaurant, number="6", is_active=False
        )
        url = reverse("public-menu", kwargs={"qr_hash": inactive_table.qr_hash})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_contains_restaurant_with_background(self):
        """TUZATISH: javobda restaurant obyekti menu_background bilan bo'lishi kerak."""
        response = self.client.get(self.url)
        self.assertIn("restaurant", response.data)
        self.assertEqual(response.data["restaurant"]["id"], self.restaurant.id)
        self.assertIn("menu_background", response.data["restaurant"])

    def test_response_contains_table_number(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["table_number"], "5")

    def test_only_active_categories_returned(self):
        response = self.client.get(self.url)
        category_names = [c["name"] for c in response.data["categories"]]
        self.assertIn("Salatlar", category_names)
        self.assertNotIn("Yashirin", category_names)

    def test_only_available_dishes_returned(self):
        response = self.client.get(self.url)
        category = response.data["categories"][0]
        dish_names = [d["name"] for d in category["dishes"]]
        self.assertIn("Sezar salati", dish_names)
        self.assertNotIn("Tugagan taom", dish_names)


class PublicOrderCreateViewTests(BaseMenuTestCase):
    """public-order-create: mijoz auth'siz buyurtma beradi."""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "public-order-create", kwargs={"qr_hash": self.table.qr_hash}
        )

    def test_no_authentication_required(self):
        data = {"items": [{"dish": self.available_dish.id, "quantity": 1}]}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_creates_order_with_correct_total(self):
        data = {"items": [{"dish": self.available_dish.id, "quantity": 3}]}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=response.data["order_id"])
        self.assertEqual(order.restaurant_id, self.restaurant.id)
        self.assertEqual(order.table_id, self.table.id)
        self.assertEqual(int(order.total_price), 135000)  # 45000 * 3

    def test_empty_items_rejected(self):
        response = self.client.post(self.url, {"items": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_unavailable_dish_rejected_and_order_deleted(self):
        """Stop-listdagi (is_available=False) taom buyurtma qilinsa, order yaratilib
        keyin o'chirilishi (rollback) va aniq xato qaytarilishi kerak."""
        data = {"items": [{"dish": self.unavailable_dish.id, "quantity": 1}]}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)
        self.assertEqual(Order.objects.count(), 0)

    def test_nonexistent_dish_rejected(self):
        data = {"items": [{"dish": 999999, "quantity": 1}]}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_dish_from_other_restaurant_rejected(self):
        other_restaurant = Restaurant.objects.create(
            name="Boshqa Rest", slug="boshqa-rest"
        )
        other_category = Category.objects.create(
            restaurant=other_restaurant, name="Boshqa", slug="boshqa"
        )
        other_dish = Dish.objects.create(
            category=other_category, name="Begona taom", price=10000
        )

        data = {"items": [{"dish": other_dish.id, "quantity": 1}]}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_qr_hash_returns_404(self):
        url = reverse("public-order-create", kwargs={"qr_hash": "nonexistent"})
        response = self.client.post(
            url, {"items": [{"dish": self.available_dish.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_multiple_items_sum_correctly(self):
        second_dish = Dish.objects.create(
            category=self.active_category, name="Kompot", price=15000
        )
        data = {
            "items": [
                {"dish": self.available_dish.id, "quantity": 2},  # 90,000
                {"dish": second_dish.id, "quantity": 1},  # 15,000
            ]
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_price"], "105000.00")