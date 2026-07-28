from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.models.manager.user_manager import UserManager


class User(AbstractUser):
    """
    Custom foydalanuvchi modeli.

    Nega kerak edi:
    - Standart Django User'da `role` (direktor/ofitsiant/oshpaz) va foydalanuvchi qaysi
      restoranga tegishli ekanini bildiradigan to'g'ridan-to'g'ri FK yo'q edi.
    - Avval faqat Restaurant.owner orqali BITTA direktor bog'lanardi — ofitsiant/oshpaz
      uchun umuman akkaunt yaratib bo'lmasdi.
    - Email orqali kirish uchun username=email "hiylasi" endi kerak emas.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Direktor"
        WAITER = "waiter", "Ofitsiant"
        CHEF = "chef", "Oshpaz"

    username = None  # email asosiy identifikator bo'lgani uchun kerak emas
    email = models.EmailField("Email", unique=True)

    restaurant = models.ForeignKey(
        "apps.Restaurant",
        related_name="staff",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Ishlaydigan restorani",
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.OWNER, verbose_name="Roli"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
