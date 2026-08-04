from django.contrib.auth.models import AbstractUser
from django.db.models import CASCADE, BooleanField, CharField, EmailField, ForeignKey
from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _

from apps.models.manager.user_manager import UserManager


class User(AbstractUser):
    """
    Custom foydalanuvchi modeli.

    Asosiy identifikator - telefon raqam (email emas).

    HISOB YARATISH IERARXIYASI (endi ochiq /register YO'Q):
        super_admin -> director yaratadi (restoranga biriktirib)
        director    -> manager yaratadi (yoki to'g'ridan-to'g'ri waiter/chef)
        manager     -> waiter/chef yaratadi

    Har bir admin (super_admin/director/manager) hisob yaratganda parolni
    o'zi belgilaydi, lekin yangi xodim birinchi marta kirganda albatta
    o'z parolini o'zgartirishga MAJBUR qilinadi - buni `must_change_password`
    bayrog'i orqali frontend aniqlaydi (GET /auth/me/ javobida keladi) va
    /auth/change-password/ orqali o'zgartiriladi.

    `employment_status` - barcha rollar (director/manager/waiter/chef) uchun
    ishlash holati. `WORKING` bo'lmagan xodim tizimga kira olmaydi (login
    vaqtida tekshiriladi).
    """

    class Role(TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        DIRECTOR = "director", _("Direktor")
        MANAGER = "manager", _("Menejer")
        WAITER = "waiter", _("Ofitsiant")
        CHEF = "chef", _("Oshpaz")

    class EmploymentStatus(TextChoices):
        WORKING = "working", _("Ishlayapti")
        FIRED = "fired", _("Ishdan haydaldi")
        RESIGNED = "resigned", _("Ishdan ketdi (o'z xohishi bilan)")

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
        _("Roli"), max_length=20, choices=Role.choices, default=Role.MANAGER
    )
    employment_status = CharField(
        _("Ish holati"),
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.WORKING,
    )
    must_change_password = BooleanField(
        _("Parolni o'zgartirishi shart"),
        default=False,
        help_text=_(
            "Admin (super_admin/director/manager) tomonidan yaratilgan "
            "hisoblar uchun True - birinchi kirishda parol o'zgartirish "
            "sahifasiga yo'naltiriladi."
        ),
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")

    @property
    def is_working(self) -> bool:
        return self.employment_status == self.EmploymentStatus.WORKING

    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"