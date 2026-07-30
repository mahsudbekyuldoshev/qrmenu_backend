from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from apps.models.restaurants import Category, Dish, Restaurant, Table
from apps.models.subscriptions import Subscription


class RestaurantSerializer(ModelSerializer):
    """
    Manager/Super Admin uchun restoran serializeri.
    `menu_background` endi Manager panel orqali yozib bo'ladigan (read-only emas) maydon —
    frontendda "Manager dashboard menyu foni o'zgartira oladi" talabi shu orqali ta'minlanadi.
    """

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "menu_background",
            "subscription_end_date",
            "owner",
            "created_at",
        )

        read_only_fields = (
            "id",
            "slug",
            "is_active",
            "subscription_end_date",
            "owner",
            "created_at",
        )

    def update(self, instance, validated_data):
        # TUZATISH: faqat 'manager' roli o'z restoranining menu_background'ini
        # o'zgartira olishi kerak — bu tekshiruv view/permission qatlamida ham
        # takrorlanadi (IsRestaurantManager), lekin xavfsizlik uchun bu yerda ham
        # bloklanmagan maydonlarni tozalab qo'yamiz.
        request = self.context.get("request")
        if request and getattr(request.user, "role", None) != "manager":
            validated_data.pop("menu_background", None)
        return super().update(instance, validated_data)


class SuperAdminRestaurantSerializer(ModelSerializer):
    """
    Super Admin dashboard uchun kengaytirilgan serializer: obuna holati bilan birga.
    Ro'yxatda "nechta restoran, qaysi trialda, muddati qachon tugaydi" ko'rsatish uchun.
    """

    plan_type = SerializerMethodField()
    subscription_days_remaining = SerializerMethodField()
    manager_phone = SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "owner",
            "manager_phone",
            "plan_type",
            "subscription_days_remaining",
            "subscription_end_date",
            "created_at",
        )
        read_only_fields = fields

    def get_plan_type(self, obj: Restaurant):
        sub: Subscription | None = getattr(obj, "subscription_info", None)
        return sub.plan_type if sub else None

    def get_subscription_days_remaining(self, obj: Restaurant):
        sub: Subscription | None = getattr(obj, "subscription_info", None)
        return sub.days_remaining if sub else None

    def get_manager_phone(self, obj: Restaurant):
        return obj.owner.phone if obj.owner_id else None


class TableSerializer(ModelSerializer):
    class Meta:
        model = Table
        fields = "id", "restaurant", "number", "qr_hash", "is_active"
        read_only_fields = "id", "restaurant", "qr_hash"


class DishSerializer(ModelSerializer):
    """
    Manager uchun taom serializeri (yaratish/tahrirlash/o'chirish).

    TUZATISH: avval `value.restaurant.owner_id != request.user.id` orqali
    tekshirilardi — bu faqat "direktor" (owner) uchun ishlagan. Endi manager
    ham, boshqa rol ham `user.restaurant` orqali bog'langani uchun tekshiruv
    `user.restaurant_id` asosida qilinadi — bu barcha rollar uchun to'g'ri ishlaydi.

    Taom qo'shish/tahrirlash huquqi FAQAT manager roliga tegishli — bu view/permission
    qatlamida (masalan IsRestaurantManager) cheklanadi; oshpaz (chef) bu serializer
    orqali umuman yozish so'rovi yubora olmasligi kerak (faqat GET/read-only).
    """

    class Meta:
        model = Dish
        fields = (
            "id",
            "category",
            "name",
            "description",
            "price",
            "image",
            "is_available",
        )

    def validate_category(self, value):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if value.restaurant_id != request.user.restaurant_id:
                raise ValidationError(
                    "Bu kategoriya sizning restoraningizga tegishli emas."
                )
        return value


class CategorySerializer(ModelSerializer):
    dishes = DishSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "restaurant",
            "name",
            "slug",
            "description",
            "is_active",
            "ordering",
            "dishes",
        )
        read_only_fields = "id", "restaurant"