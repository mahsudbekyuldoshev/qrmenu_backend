from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from restaurants.models import Category, Dish, Restaurant, Table


class Command(BaseCommand):
    help = "RestoFlow demo restoran, menyu va stollarni yaratadi"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="admin@restoflow.uz",
            defaults={
                "email": "admin@restoflow.uz",
                "first_name": "RestoFlow",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin12345")
            user.save()
            self.stdout.write(self.style.SUCCESS("Admin user: admin@restoflow.uz / admin12345"))
        else:
            self.stdout.write("Admin user allaqachon bor")

        restaurant, _ = Restaurant.objects.update_or_create(
            slug="restoflow",
            defaults={
                "name": "RestoFlow Demo",
                "is_active": True,
                "owner": user,
                "subscription_end_date": timezone.now() + timedelta(days=365),
            },
        )

        for n in range(1, 13):
            Table.objects.get_or_create(
                restaurant=restaurant,
                number=str(n),
                defaults={"is_active": True},
            )

        menu = {
            "Salatlar": [
                ("Sezar salati", "Romain, parmezan, kruton", "45000"),
                ("Yunoncha salat", "Pomidor, bodring, feta, zaytun", "42000"),
            ],
            "Shoʻrvalar": [
                ("Lagʻmon", "Mol goʻshti va sabzavotlar", "55000"),
                ("Mastava", "Guruchli shoʻrva", "38000"),
            ],
            "Asosiy taomlar": [
                ("Osh", "Anʼanaviy oʻzbek oshi", "65000"),
                ("Manti", "Bugʻda pishirilgan goʻshtli manti", "48000"),
            ],
            "Grill": [
                ("Ribeye steyk", "300g ribeye, fri", "145000"),
                ("Qoʻy shashlik", "Koʻmirda pishirilgan", "72000"),
            ],
            "Ichimliklar": [
                ("Cola 0.5L", "Sovuq ichimlik", "12000"),
                ("Kompot", "Uy kompoti", "15000"),
            ],
            "Shirinliklar": [
                ("Chizkeyk", "Rezavor sous bilan", "35000"),
                ("Asalli tort", "Kremli asalli biskvit", "32000"),
            ],
        }

        for order, (cat_name, dishes) in enumerate(menu.items(), start=1):
            category, _ = Category.objects.update_or_create(
                restaurant=restaurant,
                slug=f"cat-{order}",
                defaults={
                    "name": cat_name,
                    "is_active": True,
                    "ordering": order,
                },
            )
            for dish_name, description, price in dishes:
                Dish.objects.update_or_create(
                    category=category,
                    name=dish_name,
                    defaults={
                        "description": description,
                        "price": Decimal(price),
                        "is_available": True,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo tayyor: restaurant={restaurant.slug} id={restaurant.id}, "
                f"tables={restaurant.tables.count()}, dishes={Dish.objects.filter(category__restaurant=restaurant).count()}"
            )
        )
