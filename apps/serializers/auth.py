from typing import Optional

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.models import User
from apps.models.manager.user_manager import UserManager


class UserSerializer(ModelSerializer):
    restaurant_id = SerializerMethodField()
    restaurant_slug = SerializerMethodField()
    restaurant_name = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "first_name",
            "last_name",
            "role",
            "restaurant_id",
            "restaurant_slug",
            "restaurant_name",
        )

    @extend_schema_field(OpenApiTypes.INT)
    def get_restaurant_id(self, obj: User) -> Optional[int]:
        return obj.restaurant_id

    @extend_schema_field(OpenApiTypes.STR)
    def get_restaurant_slug(self, obj: User) -> Optional[str]:
        return obj.restaurant.slug if obj.restaurant_id else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_restaurant_name(self, obj: User) -> Optional[str]:
        return obj.restaurant.name if obj.restaurant_id else None


class RegisterSerializer(Serializer):
    """
    Oddiy /register orqali FAQAT xodimlar (Ofitsiant/Oshpaz) ro'yxatdan o'tadi.

    TUZATISH: avval bu yerda direktor o'zi bilan birga yangi restoran yaratardi
    (restaurant_name maydoni orqali). Endi frontendda "Direktor" roli register
    formasidan olib tashlandi — menejer (avvalgi "direktor") hisobini faqat
    Super Admin panel orqali restoranga biriktirib yaratadi.

    Shu sabab bu yerda `restaurant_name` maydoni yo'q va `role` faqat
    waiter/chef qiymatlarini qabul qiladi — xodim keyinchalik menejer/super
    admin tomonidan biror restoranga (`user.restaurant`) biriktiriladi.
    """

    phone = CharField(max_length=20)
    password = CharField(min_length=8, write_only=True)
    full_name = CharField(max_length=150, required=False, allow_blank=True)
    role = ChoiceField(choices=[User.Role.WAITER, User.Role.CHEF])

    def validate_phone(self, value):
        phone = UserManager.normalize_phone(value)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon roʻyxatdan oʻtgan.")
        return phone

    def create(self, validated_data):
        phone = validated_data["phone"]
        full_name = validated_data.get("full_name", "").strip()

        first_name = full_name
        last_name = ""
        if " " in full_name:
            first_name, last_name = full_name.split(" ", 1)

        user = User.objects.create_user(
            phone=phone,
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            role=validated_data["role"],
        )
        # Restaurant hali biriktirilmagan — menejer/super admin keyin tayinlaydi.
        return user


class RestoFlowTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    TUZATISH: endi custom User'da USERNAME_FIELD='phone' bo'lgani uchun DRF SimpleJWT
    o'zi avtomatik 'phone' maydonini login uchun ishlatadi (email/username emas).
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["phone"] = user.phone
        token["role"] = user.role
        if user.restaurant_id:
            token["restaurant_id"] = user.restaurant_id
            token["restaurant_slug"] = user.restaurant.slug
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
