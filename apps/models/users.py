from django.contrib.auth.models import AbstractUser
from django.db.models import CASCADE, CharField, EmailField, ForeignKey
from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _

from apps.models.manager.user_manager import UserManager


class User(AbstractUser):
    """
    Custom foydalanuvchi modeli.

    Asosiy identifikator - telefon raqam (email emas). Login/register
    +998 XX XXX XX XX formatidagi telefon raqam orqali amalga oshadi.

    Rol ierarxiyasi (yuqoridan pastga):
    - `super_admin` - platformani boshqaruvchi (restoranlar, obunalar,
      director hisoblarini yaratish). Hech qanday restaurant'ga
      bog'lanmaydi (restaurant=None).
    - `director` - restoran egasi. Har bir restoranga bitta director
      biriktiriladi (`Restaurant.owner`), faqat Super Admin panel orqali
      yaratiladi. To'liq huquqga ega: menyu, xodimlar (manager/waiter/chef
      qo'shish-o'chirish), obuna holatini ko'rish, analitika.
    - `manager` - director yoki Super Admin tomonidan qo'shiladigan
      operatsion boshqaruvchi. Menyuni tahrirlaydi, buyurtmalarni
      kuzatadi, lekin xodim qo'sha olmaydi va obunani boshqara olmaydi
      (permissions.py qatlamida cheklanadi).
    - `waiter` (ofitsiant) - buyurtma qabul qiladi/yetkazadi.
    - `chef` (oshpaz) - menyuni faqat ko'radi, KDS orqali buyurtma
      holatini yangilaydi. Menyuni tahrirlash huquqi yo'q.
    """

    class Role(TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        DIRECTOR = "director", _("Direktor")
        MANAGER = "manager", _("Menejer")
        WAITER = "waiter", _("Ofitsiant")
        CHEF = "chef", _("Oshpaz")

    email = EmailField(_("Email"), blank=True, null=True)
    phone = CharField(
        _("Telefon raqam"),
        max_length=20,
        unique=True,
        help_text=_("Format: +998XXXXXXXXX"),
    )

    restaurant = ForeignKey(
        "apps.Restaurant",
        CASCADE,
        related_name="staff",
        null=True,
        blank=True,
        verbose_name=_("Ishlaydigan restorani"),
        help_text=_("Super Admin uchun bo'sh qoldiriladi."),
    )
    role = CharField(
        _("Roli"),
        max_length=20,
        choices=Role.choices,
        default=Role.MANAGER,
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")

    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"