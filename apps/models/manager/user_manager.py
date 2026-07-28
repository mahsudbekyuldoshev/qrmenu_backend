from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Email orqali autentifikatsiya qiluvchi custom foydalanuvchi manageri.

    Avval RegisterSerializer'da `username=email` qilib "hiylakorlik" qilingan edi —
    bu Django'ning standart User modeli username maydonini talab qilgani uchun kerak
    bo'lgan vaqtinchalik yechim. Custom User + shu manager bilan email tabiiy ravishda
    asosiy identifikator bo'ladi, hech qanday yamoq kerak emas.
    """

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email kiritilishi shart.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser uchun is_staff=True bo'lishi shart.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser uchun is_superuser=True bo'lishi shart.")

        return self._create_user(email, password, **extra_fields)