from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Telefon raqam orqali autentifikatsiya qiluvchi custom foydalanuvchi manageri.

    Avval email asosiy identifikator edi, endi frontend telefon raqam orqali
    login/register qiladi (+998 XX XXX XX XX formatida). Shuning uchun asosiy
    identifikator email emas, `phone` maydoni bo'ladi. Email endi ixtiyoriy
    (bo'sh bo'lishi mumkin) - faqat bildirishnomalar yoki hisobot uchun saqlanadi.
    """

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam kiritilishi shart.")
        phone = self.normalize_phone(phone)
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
            raise ValueError("Superuser uchun is_staff=True bo'lishi shart.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser uchun is_superuser=True bo'lishi shart.")

        return self._create_user(phone, password, **extra_fields)
