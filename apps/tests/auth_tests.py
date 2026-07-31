from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.models import User


class RegisterTests(APITestCase):
    """auth-register: faqat waiter/chef ro'yxatdan o'ta oladi, restoran biriktirilmagan holda."""

    def setUp(self):
        self.url = reverse("auth-register")

    def test_register_waiter_success(self):
        data = {
            "phone": "+998901234567",
            "password": "password123",
            "full_name": "Aziza Karimova",
            "role": User.Role.WAITER,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(phone="+998901234567")
        self.assertEqual(user.role, User.Role.WAITER)
        self.assertIsNone(user.restaurant_id)  # hali biriktirilmagan
        self.assertEqual(user.first_name, "Aziza")
        self.assertEqual(user.last_name, "Karimova")

    def test_register_chef_success(self):
        data = {
            "phone": "+998907654321",
            "password": "password123",
            "full_name": "Rustam Ahmedov",
            "role": User.Role.CHEF,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone="+998907654321")
        self.assertEqual(user.role, User.Role.CHEF)

    def test_register_manager_role_rejected(self):
        """Frontend endi 'manager' rolini register'da bermaydi, lekin backend ham
        rad etishi shart — RegisterSerializer.role faqat WAITER/CHEF qabul qiladi."""
        data = {
            "phone": "+998901112233",
            "password": "password123",
            "role": User.Role.MANAGER,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_register_super_admin_role_rejected(self):
        data = {
            "phone": "+998901112244",
            "password": "password123",
            "role": User.Role.SUPER_ADMIN,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone_rejected(self):
        User.objects.create_user(
            phone="+998901234567", password="pass1234", role=User.Role.WAITER
        )
        data = {
            "phone": "+998901234567",
            "password": "password123",
            "role": User.Role.CHEF,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_register_phone_normalization(self):
        """Foydalanuvchi '+998 90 123 45 67' kabi bo'shliqli formatda kiritsa ham,
        UserManager.normalize_phone orqali '+998901234567'ga tozalanishi kerak."""
        data = {
            "phone": "+998 90 123 45 67",
            "password": "password123",
            "role": User.Role.WAITER,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(phone="+998901234567").exists())

    def test_register_missing_required_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)
        self.assertIn("password", response.data)
        self.assertIn("role", response.data)

    def test_register_short_password_rejected(self):
        data = {
            "phone": "+998901234599",
            "password": "short",
            "role": User.Role.WAITER,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


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