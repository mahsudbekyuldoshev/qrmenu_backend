from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.models.manager.user_manager import UserManager


class User(AbstractUser):
    """
    Custom foydalanuvchi modeli.
    Frontend yangilanishiga mos o'zgarishlar:
    - Endi telefon raqam asosiy identifikator (email emas). Login/register
      +998 XX XXX XX XX formatidagi telefon raqam orqali amalga oshadi.
    - "Direktor" (owner) roli endi oddiy /register orqali yaratilmaydi -
      role nomi `manager`ga o'zgartirildi va faqat Super Admin panel orqali
      biriktiriladi (restoranga manager tayinlash).
    - Yangi `super_admin` roli qo'shildi - platformani boshqaruvchi (restoranlar,
      obunalar, manager hisoblarini yaratish) uchun. Bu foydalanuvchi hech qanday
      restaurant'ga bog'lanmaydi (restaurant=None).
    - `chef` (oshpaz) endi menyuni faqat ko'radi - tahrirlash huquqi frontendda
      olib tashlandi (backend darajasida ham permission tekshiruvi kerak,
      views.py/permissions.py qatlamida cheklanadi).
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        MANAGER = "manager", "Menejer"  # avvalgi "owner"/"Direktor"
        WAITER = "waiter", "Ofitsiant"
        CHEF = "chef", "Oshpaz"

    username = None  # endi kerak emas
    email = models.EmailField("Email", blank=True, null=True)

    phone = models.CharField(
        "Telefon raqam",
        max_length=20,
        unique=True,
        help_text="Format: +998XXXXXXXXX",
    )

    restaurant = models.ForeignKey(
        "apps.Restaurant",
        related_name="staff",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Ishlaydigan restorani",
        help_text="Super Admin uchun bo'sh qoldiriladi.",
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.MANAGER, verbose_name="Roli"
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"
