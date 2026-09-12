import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.models import User
from apps.models.restaurants import Category, Dish, Restaurant, Table
from apps.utils.slugs import unique_restaurant_slug

DEMO_PASSWORD = "demo1234"

RESTAURANTS = [
    ("Toshkent Grill", "Tashkent Grill"),
    ("Samarqand Oshxonasi", "Samarkand Plov House"),
    ("Buxoro Saroyi", "Bukhara Courtyard"),
    ("Chorsu Taomlari", "Chorsu Cafe"),
    ("Ipak Yo'li", "Silk Road Kitchen"),
]

MENU_VARIATIONS = [
    {
        "cat": "Gril",
        "dishes": [
            ("Steak", "Mol go'shtidan", "120000", True),
            ("Burger", "Tovuqli", "55000", True),
        ]
    },
    {
        "cat": "Milliy",
        "dishes": [
            ("Osh", "To'y oshi", "70000", True),
            ("Somsa", "Tandir somsa", "15000", True),
        ]
    },
    {
        "cat": "Sharqona",
        "dishes": [
            ("Lagmon", "Cho'zma lagmon", "45000", True),
            ("Manti", "Qaymoqli", "40000", True),
        ]
    },
    {
        "cat": "Fast Food",
        "dishes": [
            ("Pizza", "Pepperoni", "85000", True),
            ("Lavash", "Mol go'shtli", "35000", True),
        ]
    },
    {
        "cat": "Evropa",
        "dishes": [
            ("Pasta", "Karbonara", "65000", True),
            ("Salat", "Sezar", "50000", True),
        ]
    },
]

class Command(BaseCommand):
    help = "Toza demo: 5 restoran, 5 direktor, 5 manager, 5 waiter, 5 chef, kategoriyalar va taomlar"

    def handle(self, *args, **options):
        # 1. Clear existing data (handled by flush before run)

        # 2. Seed data
        for i, (name, slug_name) in enumerate(RESTAURANTS):
            # Director
            director = self._upsert_user(
                f"90100000{i+1}", User.Role.DIRECTOR, f"Director{i+1}", f"Surname{i+1}"
            )
            # Restaurant
            restaurant = self._upsert_restaurant(name, director)
            director.restaurant = restaurant
            director.save(update_fields=['restaurant'])
            
            # Staff
            for role_idx, (role, first_name) in enumerate([
                (User.Role.MANAGER, f"Manager{i+1}"),
                (User.Role.WAITER, f"Waiter{i+1}"),
                (User.Role.CHEF, f"Chef{i+1}"),
            ]):
                # Full 9 digits after +998:
                # 90 + role_base(2,3,4) + i + 1 (3 digits) -> e.g. 90 200 001
                # Final: 90 200 000 + i + 1 + (role_idx * 1000000)
                # Let's make it simple and unique: 99 + role_idx(2,3,4) + i+1(000) + 000
                phone9 = f"99{role_idx+2}{i+1:03d}000"
                self._upsert_user(
                    phone9, role, first_name, f"Surname{i+1}", restaurant=restaurant
                )
            
            # Tables
            for n in range(1, 6):
                Table.objects.create(restaurant=restaurant, number=str(n))

            # Menu
            self._seed_menu(restaurant, i)
            
            # Print QR info
            first_table = restaurant.tables.first()
            self.stdout.write(self.style.NOTICE(f"  Restoran: {restaurant.name} | Stol: {first_table.number} | QR Hash: {first_table.qr_hash}"))
            self.stdout.write(self.style.NOTICE(f"  URL: http://localhost:8000/menu/{first_table.qr_hash}/"))

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar muvaffaqiyatli yuklandi!"))

    def _upsert_user(self, phone9, role, first, last, restaurant=None):
        phone = f"+998{phone9}"
        user, _ = User.objects.get_or_create(
            phone=phone,
            defaults={
                "username": phone,
                "first_name": first,
                "last_name": last,
                "role": role,
                "must_change_password": False,
            },
        )
        user.set_password(DEMO_PASSWORD)
        if restaurant:
            user.restaurant = restaurant
        user.save()
        return user

    def _upsert_restaurant(self, name, director):
        slug = unique_restaurant_slug(name, preferred=slugify(name))
        return Restaurant.objects.create(name=name, slug=slug, owner=director, is_active=True)

    def _seed_menu(self, restaurant, index):
        cat_data = MENU_VARIATIONS[index]
        category = Category.objects.create(
            restaurant=restaurant, name=cat_data["cat"], ordering=1
        )
        for dish_name, desc, price, kitchen in cat_data["dishes"]:
            Dish.objects.create(
                category=category, name=dish_name, description=desc, price=Decimal(price), requires_kitchen=kitchen
            )
