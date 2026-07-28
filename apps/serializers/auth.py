from typing import Optional

from django.utils.text import slugify
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.models import Restaurant, User


class UserSerializer(ModelSerializer):
    restaurant_id = SerializerMethodField()
    restaurant_slug = SerializerMethodField()
    restaurant_name = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "restaurant_id",
            "restaurant_slug",
            "restaurant_name",
        )

    # TUZATISH: avval `obj.owned_restaurants.order_by("id").first()` orqali (teskari FK
    # qidiruv, faqat direktorga ishlagan) topilardi. Endi User.restaurant to'g'ridan-to'g'ri
    # FK bo'lgani uchun oddiy va HAR QANDAY rol (direktor/ofitsiant/oshpaz) uchun ishlaydi.

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
    Faqat DIREKTOR shu orqali ro'yxatdan o'tadi (o'zi bilan birga yangi restoran yaratadi).
    Ofitsiant/oshpaz akkauntlari alohida — direktor ularni keyinchalik
    (masalan InviteStaffView orqali, hozircha yozilmagan) qo'shadi.
    """

    email = EmailField()
    password = CharField(min_length=8, write_only=True)
    full_name = CharField(max_length=150, required=False, allow_blank=True)
    restaurant_name = CharField(max_length=255)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Bu email allaqachon roʻyxatdan oʻtgan.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        full_name = validated_data.get("full_name", "").strip()
        restaurant_name = validated_data["restaurant_name"].strip()

        first_name = full_name
        last_name = ""
        if " " in full_name:
            first_name, last_name = full_name.split(" ", 1)

        # TUZATISH: endi `username=email` hiylasi kerak emas — custom User modelida
        # email o'zi USERNAME_FIELD.
        user = User.objects.create_user(
            email=email,
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            role=User.Role.OWNER,
        )

        base_slug = slugify(restaurant_name) or "restaurant"
        slug = base_slug
        i = 1
        while Restaurant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{i}"
            i += 1

        restaurant = Restaurant.objects.create(
            name=restaurant_name,
            slug=slug,
            owner=user,
            is_active=True,
        )
        user.restaurant = restaurant
        user.save(update_fields=["restaurant"])
        return user


class RestoFlowTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    TUZATISH: avval `__init__`da `username` maydonini ixtiyoriy qilib, `email` maydonini
    qo'lda qo'shish kerak edi (chunki standart User'da USERNAME_FIELD='username' edi).
    Endi custom User'da USERNAME_FIELD='email' bo'lgani uchun DRF SimpleJWT o'zi avtomatik
    'email' maydonini yaratadi — hech qanday qo'shimcha hiyla kerak emas.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        if user.restaurant_id:
            token["restaurant_id"] = user.restaurant_id
            token["restaurant_slug"] = user.restaurant.slug
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
