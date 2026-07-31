from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models import Category, Dish, Restaurant, Table, User


class BaseRestaurantTestCase(APITestCase):
    """Umumiy setUp: bitta restoran, manager, waiter, chef, boshqa restoranga
    tegishli 'begona' xodim (tenant izolyatsiyasini tekshirish uchun)."""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Rayhon", slug="rayhon")
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
        self.other_manager = User.objects.create_user(
            phone="+998900000004",
            password="password123",
            role=User.Role.MANAGER,
            restaurant=self.other_restaurant,
        )

        self.category = Category.objects.create(
            restaurant=self.restaurant, name="Salatlar", slug="salatlar"
        )
        self.dish = Dish.objects.create(
            category=self.category, name="Sezar salati", price=45000
        )


class MyRestaurantViewTests(BaseRestaurantTestCase):
    """restaurant-me: GET har qanday xodim uchun, PATCH faqat manager uchun."""

    def setUp(self):
        super().setUp()
        self.url = reverse("restaurant-me")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_can_view(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.restaurant.id)

    def test_waiter_can_view(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chef_can_view(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_without_restaurant_gets_403(self):
        orphan = User.objects.create_user(
            phone="+998900000099", password="password123", role=User.Role.WAITER
        )
        self.client.force_authenticate(user=orphan)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_update_menu_background(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            self.url, {"name": "Rayhon Milliy Taomlar"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, "Rayhon Milliy Taomlar")

    def test_waiter_cannot_update(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.patch(self.url, {"name": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chef_cannot_update(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.patch(self.url, {"name": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TableViewSetTests(BaseRestaurantTestCase):
    """table-list / table-detail: faqat manager boshqaradi."""

    def setUp(self):
        super().setUp()
        self.list_url = reverse("table-list")
        self.table = Table.objects.create(restaurant=self.restaurant, number="1")

    def test_manager_can_create_table(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(self.list_url, {"number": "5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Table.objects.filter(restaurant=self.restaurant, number="5").exists()
        )

    def test_waiter_cannot_create_table(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.post(self.list_url, {"number": "6"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chef_cannot_create_table(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.post(self.list_url, {"number": "7"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_sees_only_own_restaurant_tables(self):
        Table.objects.create(restaurant=self.other_restaurant, number="99")
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        numbers = [t["number"] for t in response.data]
        self.assertIn("1", numbers)
        self.assertNotIn("99", numbers)

    def test_manager_can_delete_table(self):
        detail_url = reverse("table-detail", kwargs={"pk": self.table.id})
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Table.objects.filter(id=self.table.id).exists())

    def test_qr_hash_is_read_only_on_create(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            self.list_url,
            {"number": "10", "qr_hash": "hacked-hash"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["qr_hash"], "hacked-hash")


class CategoryViewSetTests(BaseRestaurantTestCase):
    """category-list / category-detail: o'qish - barcha xodim, yozish - faqat manager."""

    def setUp(self):
        super().setUp()
        self.list_url = reverse("category-list")
        self.detail_url = reverse("category-detail", kwargs={"pk": self.category.id})

    def test_manager_can_list(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_waiter_can_list_read_only(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chef_can_list_but_not_write(self):
        """Talab: oshpaz menyuni ko'radi, lekin qo'sha/o'zgartira olmaydi."""
        self.client.force_authenticate(user=self.chef)

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            self.list_url, {"name": "Yangi kategoriya", "slug": "yangi"}, format="json"
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        update_response = self.client.patch(
            self.detail_url, {"name": "Hack"}, format="json"
        )
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

        delete_response = self.client.delete(self.detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            self.list_url, {"name": "Ichimliklar", "slug": "ichimliklar"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # restaurant avtomatik biriktiriladi (perform_create)
        self.assertEqual(response.data["restaurant"], self.restaurant.id)

    def test_tenant_isolation_on_list(self):
        Category.objects.create(
            restaurant=self.other_restaurant, name="Begona", slug="begona"
        )
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.list_url)
        names = [c["name"] for c in response.data]
        self.assertNotIn("Begona", names)


class DishViewSetTests(BaseRestaurantTestCase):
    """dish-list / dish-detail: o'qish - barcha xodim, yozish - faqat manager."""

    def setUp(self):
        super().setUp()
        self.list_url = reverse("dish-list")
        self.detail_url = reverse("dish-detail", kwargs={"pk": self.dish.id})

    def test_chef_can_view_dishes_read_only(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chef_cannot_create_dish(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.post(
            self.list_url,
            {"category": self.category.id, "name": "Yangi taom", "price": 10000},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chef_cannot_update_dish(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.patch(
            self.detail_url, {"price": 99999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chef_cannot_delete_dish(self):
        self.client.force_authenticate(user=self.chef)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create_dish(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            self.list_url,
            {"category": self.category.id, "name": "Lag'mon", "price": 55000},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_can_update_dish(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            self.detail_url, {"price": 48000}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dish.refresh_from_db()
        self.assertEqual(int(self.dish.price), 48000)

    def test_manager_can_delete_dish(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_manager_cannot_assign_category_from_other_restaurant(self):
        """DishSerializer.validate_category: category.restaurant_id != user.restaurant_id."""
        other_category = Category.objects.create(
            restaurant=self.other_restaurant, name="Begona kat", slug="begona-kat"
        )
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            self.list_url,
            {"category": other_category.id, "name": "Hack taom", "price": 1000},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

    def test_waiter_cannot_write_dish(self):
        self.client.force_authenticate(user=self.waiter)
        response = self.client.post(
            self.list_url,
            {"category": self.category.id, "name": "X", "price": 1000},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)