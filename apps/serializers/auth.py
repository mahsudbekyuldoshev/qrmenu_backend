from typing import Optional

from django.contrib.auth.password_validation import validate_password
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.models import User


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
            "employment_status",
            "must_change_password",
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


class RestoFlowTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    USERNAME_FIELD='phone' bo'lgani uchun DRF SimpleJWT avtomatik 'phone'
    maydonini login uchun ishlatadi.

    TUZATISH: endi ochiq /register YO'Q - barcha hisoblar
    super_admin/director/manager tomonidan yaratiladi. Shu sabab bu yerda
    QO'SHIMCHA tekshiruv bor - `employment_status != WORKING` bo'lgan
    xodim (ishdan bo'shatilgan/ketgan) LOGIN QILA OLMAYDI, garchi
    is_active hali True bo'lsa ham (ikki qavatli himoya).
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

        if self.user.role != User.Role.SUPER_ADMIN and not self.user.is_working:
            raise AuthenticationFailed(
                "Sizning hisobingiz faol emas (ishdan bo'shatilgan/ketgan). "
                "Restoran rahbariyatiga murojaat qiling."
            )

        data["user"] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(Serializer):
    """
    POST /auth/change-password/
    Har qanday login qilgan foydalanuvchi o'z parolini o'zgartiradi.
    Admin tomonidan yaratilgan hisoblar (`must_change_password=True`)
    birinchi kirishda shu endpointga majburiy yo'naltiriladi (frontend
    tomonidan - backend buni bloklamaydi, faqat bayroqni ko'rsatadi).
    """

    old_password = CharField(write_only=True)
    new_password = CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise ValidationError("Joriy parol noto'g'ri.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return user
