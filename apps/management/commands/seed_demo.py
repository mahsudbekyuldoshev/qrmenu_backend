from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.models import User
from apps.models.restaurants import Category, Dish, Restaurant, Table
from apps.models.subscriptions import Payment, Subscription
from apps.serializers.super_admin import add_months
from apps.utils.slugs import unique_restaurant_slug


DEMO_PASSWORD = "demo1234"

CORE_USERS = [
    ("909998877", User.Role.SUPER_ADMIN, "Super", "Admin"),
    ("901234567", User.Role.DIRECTOR, "Aziza", "Karimova"),
    ("901112233", User.Role.MANAGER, "Madina", "Manager"),
    ("900001122", User.Role.WAITER, "Sardor", "Waiter"),
    ("907654321", User.Role.CHEF, "Jasur", "Chef"),
]

DIRECTOR_EXTRAS = [
    ("910000002", "Bekzod", "Ergashev"),
    ("910000003", "Dilnoza", "Rahimova"),
    ("910000004", "Jasur", "Toshpulatov"),
    ("910000005", "Malika", "Yusupova"),
    ("910000006", "Nodir", "Alimov"),
    ("910000007", "Sevara", "Qodirova"),
    ("910000008", "Timur", "Ismoilov"),
    ("910000009", "Umida", "Nazarova"),
    ("910000010", "Farrux", "Saidov"),
]

RESTAURANT_NAMES = [
    "RestoFlow Demo",
    "Samarkand Plov House",
    "Tashkent Grill",
    "Bukhara Courtyard",
    "Chorsu Cafe",
    "Silk Road Kitchen",
    "Anhor Terrace",
    "Navruz Garden",
    "Oshxona Milliy",
    "Lagmon House",
    "Somsa Corner",
    "Cafe Alfraganus",
    "Everest Bistro",
    "Leader Kitchen",
    "Progress Cafe",
    "Cambridge Lounge",
    "IQ Gastro",
    "Zamon Taste",
    "Novda Kitchen",
    "Central Dining",
]

# 10 director → jami 20 restoran
OWNERSHIP = [3, 3, 2, 2, 2, 2, 2, 2, 1, 1]

MENU = {
    "Salatlar": [
        ("Sezar salati", "Romain, parmezan, kruton", "45000", True),
        ("Yunoncha salat", "Pomidor, bodring, feta", "42000", True),
    ],
    "Asosiy": [
        ("Osh", "An'anaviy o'zbek oshi", "65000", True),
        ("Manti", "Bug'da pishirilgan", "48000", True),
        ("Shashlik", "Ko'mirda pishirilgan", "72000", True),
    ],
    "Ichimliklar": [
        ("Cola 0.5L", "Sovuq ichimlik", "12000", False),
        ("Kompot", "Uy kompoti", "15000", False),
    ],
}


class Command(BaseCommand):
    help = "Boy demo: 10 direktor, 20 restoran, to'lovlar va xodimlar"

    def handle(self, *args, **options):
        now = timezone.now()
        core: dict[str, User] = {}

        for phone9, role, first, last in CORE_USERS:
            user = self._upsert_user(
                phone9, role, first, last, email=f"{phone9}@restoflow.uz"
            )
            core[phone9] = user
            self.stdout.write(self.style.SUCCESS(f"  core {user.phone} ({role})"))

        directors: list[User] = [core["901234567"]]
        for phone9, first, last in DIRECTOR_EXTRAS:
            user = self._upsert_user(
                phone9,
                User.Role.DIRECTOR,
                first,
                last,
                email=f"{phone9}@restoflow.uz",
            )
            directors.append(user)
            self.stdout.write(self.style.SUCCESS(f"  director {user.phone}"))

        restaurants: list[Restaurant] = []
        name_i = 0
        for dir_i, count in enumerate(OWNERSHIP):
            director = directors[dir_i]
            for j in range(count):
                name = RESTAURANT_NAMES[name_i]
                name_i += 1
                restaurant = self._upsert_restaurant(name, director)
                if not director.restaurant_id:
                    director.restaurant = restaurant
                    director.save(update_fields=["restaurant"])

                months = random.choice([1, 3, 6, 12])
                expired = random.random() < 0.15
                end = add_months(now, -1 if expired else months)
                sub, _ = Subscription.objects.update_or_create(
                    restaurant=restaurant,
                    defaults={
                        "price": Decimal("299000.00"),
                        "is_active": True,
                        "end_date": end,
                    },
                )

                # Eski to'lovlarni tozalab, yangisini yozamiz (re-run uchun)
                sub.payments.all().delete()
                for m_ago in range(random.randint(5, 11)):
                    paid_at = add_months(now, -m_ago)
                    amount = Decimal(str(random.choice([299000, 598000, 897000])))
                    p = Payment.objects.create(
                        subscription=sub,
                        amount=amount,
                        period_months=Decimal("1"),
                        note=f"Demo {m_ago} oy oldin",
                    )
                    Payment.objects.filter(pk=p.pk).update(paid_at=paid_at)

                for n in range(1, random.randint(8, 14)):
                    Table.objects.get_or_create(
                        restaurant=restaurant,
                        number=str(n),
                        defaults={"is_active": True},
                    )

                if dir_i == 0 and j == 0:
                    self._seed_menu(restaurant)

                restaurants.append(restaurant)
                self.stdout.write(
                    f"  resto {len(restaurants):02d} {restaurant.name} → {director.phone}"
                )

        primary = restaurants[0]
        for phone9 in ("901112233", "900001122", "907654321"):
            u = core[phone9]
            u.restaurant = primary
            u.save(update_fields=["restaurant"])

        staff_n = 0
        for resto in restaurants[:6]:
            for role, prefix in (
                (User.Role.MANAGER, "94"),
                (User.Role.WAITER, "95"),
                (User.Role.CHEF, "97"),
            ):
                staff_n += 1
                phone9 = f"{prefix}{staff_n:07d}"
                self._upsert_user(
                    phone9,
                    role,
                    f"{str(role).replace('_', ' ').title()}{staff_n}",
                    resto.name.split()[0][:20],
                    restaurant=resto,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTayyor: directors={len(directors)}, restaurants={len(restaurants)}, "
                f"payments={Payment.objects.count()}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Parol: {DEMO_PASSWORD}\n"
                "  Super Admin 90 999 88 77 | Director 90 123 45 67\n"
                "  Manager 90 111 22 33 | Waiter 90 000 11 22 | Chef 90 765 43 21"
            )
        )

    def _upsert_user(
        self,
        phone9: str,
        role: str,
        first: str,
        last: str,
        *,
        email: str = "",
        restaurant: Restaurant | None = None,
    ) -> User:
        phone = f"+998{phone9}"
        user, _ = User.objects.get_or_create(
            phone=phone,
            defaults={
                "username": phone,
                "first_name": first,
                "last_name": last,
                "role": role,
                "email": email or f"{phone9}@restoflow.uz",
                "must_change_password": False,
                "is_staff": role == User.Role.SUPER_ADMIN,
                "is_superuser": role == User.Role.SUPER_ADMIN,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.role = role
        user.first_name = first
        user.last_name = last
        user.email = email or user.email or f"{phone9}@restoflow.uz"
        user.must_change_password = False
        user.is_staff = role == User.Role.SUPER_ADMIN
        user.is_superuser = role == User.Role.SUPER_ADMIN
        if restaurant is not None:
            user.restaurant = restaurant
        user.save()
        return user

    def _upsert_restaurant(self, name: str, director: User) -> Restaurant:
        existing = Restaurant.objects.filter(name=name).first()
        if existing:
            existing.owner = director
            existing.is_active = True
            existing.save(update_fields=["owner", "is_active"])
            return existing
        slug = unique_restaurant_slug(name, preferred=slugify(name) or None)
        return Restaurant.objects.create(
            name=name,
            slug=slug,
            is_active=True,
            owner=director,
        )

    def _seed_menu(self, restaurant: Restaurant):
        for order, (cat_name, dishes) in enumerate(MENU.items(), start=1):
            category, _ = Category.objects.update_or_create(
                restaurant=restaurant,
                slug=f"cat-{order}",
                defaults={
                    "name": cat_name,
                    "is_active": True,
                    "ordering": order,
                },
            )
            for dish_name, description, price, requires_kitchen in dishes:
                Dish.objects.update_or_create(
                    category=category,
                    name=dish_name,
                    defaults={
                        "description": description,
                        "price": Decimal(price),
                        "is_available": True,
                        "requires_kitchen": requires_kitchen,
                    },
                )
