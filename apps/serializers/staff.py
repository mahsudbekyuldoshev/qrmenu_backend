import secrets
import string

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models.manager.user_manager import UserManager
from apps.models.users import User


def generate_random_password(length: int = 12) -> str:
    """Django versiyalari orasida barqaror ishlashi uchun o'zimizning
    xavfsiz tasodifiy parol generatorimiz (`secrets` moduli, kriptografik
    jihatdan xavfsiz)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# Kim kimni yaratishi/ko'rishi mumkinligi shu yerda markazlashtirilgan -
# StaffViewSet ham shu xaritadan foydalanadi.
CREATABLE_ROLES_BY_CREATOR = {
    User.Role.DIRECTOR: (User.Role.MANAGER, User.Role.WAITER, User.Role.CHEF),
    User.Role.MANAGER: (User.Role.WAITER, User.Role.CHEF),
}


class StaffCreateSerializer(Serializer):
    """
    Director yoki manager o'z restoraniga yangi xodim qo'shadi.
    Restoran avtomatik `request.user.restaurant` dan olinadi - frontend
    buni yubormaydi.

    Parolni ADMIN o'zi belgilaydi (yoki bo'sh qoldirilsa, tasodifiy parol
    generatsiya qilinadi va javobda BIR MARTA qaytariladi - keyin qayta
    ko'rsatilmaydi). Yaratilgan xodim `must_change_password=True` bilan
    boshlanadi.
    """

    phone = CharField(max_length=20)
    password = CharField(min_length=8, write_only=True, required=False, allow_blank=True)
    first_name = CharField(max_length=150, required=False, allow_blank=True)
    last_name = CharField(max_length=150, required=False, allow_blank=True)
    role = ChoiceField(choices=User.Role.choices)

    def validate_phone(self, value):
        phone = UserManager.normalize_phone(value)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon roʻyxatdan oʻtgan.")
        return phone

    def validate_role(self, value):
        creator = self.context["request"].user
        allowed = CREATABLE_ROLES_BY_CREATOR.get(creator.role, ())
        if value not in allowed:
            raise ValidationError(
                f"Sizning rolingiz ({creator.get_role_display()}) '{value}' "
                f"rolini yarata olmaydi."
            )
        return value

    def create(self, validated_data):
        creator = self.context["request"].user
        password = validated_data.get("password") or generate_random_password(12)

        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=validated_data["role"],
            restaurant=creator.restaurant,
            must_change_password=True,
        )
        # Agar parol admin tomonidan berilmagan bo'lsa - generatsiya
        # qilingan parolni javobda bir marta ko'rsatish uchun saqlaymiz.
        user._generated_password = None if validated_data.get("password") else password
        return user


class StaffSerializer(ModelSerializer):
    """Xodimlar ro'yxati/detali/tahrirlash uchun (parolsiz)."""

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "first_name",
            "last_name",
            "role",
            "employment_status",
            "is_active",
            "must_change_password",
            "date_joined",
        )
        read_only_fields = ("id", "phone", "role", "must_change_password", "date_joined")

    def validate(self, attrs):
        # Rol o'zgartirishga bu serializer orqali ruxsat berilmaydi - faqat
        # employment_status/ism-familiya. Rolni almashtirish xohlansa,
        # xodimni o'chirib qayta yaratish tavsiya etiladi (xavfsizroq).
        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Ishdan bo'shatilgan/ketgan xodim tizimga kira olmasin.
        instance.is_active = instance.employment_status == User.EmploymentStatus.WORKING
        instance.save(update_fields=["is_active"])
        return instance