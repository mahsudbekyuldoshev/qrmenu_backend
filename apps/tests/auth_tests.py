from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth-register")
        self.login_url = reverse("auth-login")

    def test_register(self):
        data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "restaurant_name": "Test Restaurant",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("access" in response.data)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_login(self):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="password123",
        )
        data = {"email": "test@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in response.data)
