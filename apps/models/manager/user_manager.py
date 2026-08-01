from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Telefon raqam orqali autentifikatsiya qiluvchi custom foydalanuvchi manageri.

    Asosiy identifikator - email emas, `phone` maydoni (+998 XX XXX XX XX
    formatida). Email endi ixtiyoriy - faqat bildirishnoma/hisobot uchun.
    """

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError(_("Telefon raqam kiritilishi shart."))
        phone = self.normalize_phone(phone)
        # `AbstractUser`dan meros qolgan `username` maydoni hali ham
        # unique=True - agar to'ldirilmasa, barcha userlarda username=""
        # bo'lib qolib, IKKINCHI foydalanuvchi yaratilganda unique constraint
        # xatosiga olib keladi. Shuning uchun uni ham `phone`ga tenglashtirib
        # qo'yamiz (foydalanuvchi username orqali kirmaydi, USERNAME_FIELD
        # baribir "phone").
        extra_fields.setdefault("username", phone)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Telefon raqamni +998XXXXXXXXX ko'rinishiga keltiradi.
        Frontend "+998 90 065 60 09" kabi formatlangan holda yuborishi mumkin,
        shuning uchun bo'shliqlarni tozalab, yagona formatga keltiramiz.
        """
        digits = "".join(ch for ch in phone if ch.isdigit())
        if not digits.startswith("998"):
            digits = "998" + digits.lstrip("0")
        return f"+{digits}"

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "super_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser uchun is_staff=True bo'lishi shart."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser uchun is_superuser=True bo'lishi shart."))

        return self._create_user(phone, password, **extra_fields)