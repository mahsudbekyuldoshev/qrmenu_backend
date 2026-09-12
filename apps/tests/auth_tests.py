from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models import User


# Registration tests removed because the public /auth/register/ endpoint was removed.
# Registration is now handled through staff creation hierarchy.


class LoginTests(APITestCase):
    """auth-login: telefon raqam + parol orqali JWT token olish."""

    def setUp(self):
        self.url = reverse("auth-login")
        self.password = "password123"
        self.user = User.objects.create_user(
            phone="+998901234567",
            password=self.password,
            role=User.Role.MANAGER,
        )

    def test_login_success(self):
        data = {"phone": "+998901234567", "password": self.password}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["phone"], "+998901234567")
        self.assertEqual(response.data["user"]["role"], User.Role.MANAGER)

    def test_login_wrong_password(self):
        data = {"phone": "+998901234567", "password": "wrong-password"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_phone(self):
        data = {"phone": "+998900000000", "password": self.password}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_token_contains_role_and_restaurant(self):
        from apps.models import Restaurant

        restaurant = Restaurant.objects.create(name="Test Rest", slug="test-rest")
        self.user.restaurant = restaurant
        self.user.save(update_fields=["restaurant"])

        data = {"phone": "+998901234567", "password": self.password}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["restaurant_id"], restaurant.id)
        self.assertEqual(response.data["user"]["restaurant_slug"], "test-rest")


class TokenRefreshTests(APITestCase):
    """auth-refresh: refresh token orqali yangi access token olish."""

    def setUp(self):
        self.login_url = reverse("auth-login")
        self.refresh_url = reverse("auth-refresh")
        self.password = "password123"
        User.objects.create_user(
            phone="+998901234567", password=self.password, role=User.Role.WAITER
        )

    def test_refresh_success(self):
        login_response = self.client.post(
            self.login_url,
            {"phone": "+998901234567", "password": self.password},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_invalid_token(self):
        response = self.client.post(
            self.refresh_url, {"refresh": "invalid-token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(APITestCase):
    """auth-me: joriy foydalanuvchi ma'lumotini olish."""

    def setUp(self):
        self.url = reverse("auth-me")
        self.user = User.objects.create_user(
            phone="+998901234567",
            password="password123",
            role=User.Role.CHEF,
            first_name="Rustam",
        )

    def test_me_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], "+998901234567")
        self.assertEqual(response.data["role"], User.Role.CHEF)
        self.assertEqual(response.data["first_name"], "Rustam")