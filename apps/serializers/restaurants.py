from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer

from apps.models.restaurants import Category, Dish, Restaurant, Table
from apps.models.subscriptions import Subscription
from apps.models.users import User
from apps.utils.slugs import unique_restaurant_slug


class RestaurantSerializer(ModelSerializer):
    """
    Restoran serializeri. GET - director/manager/waiter/chef hammasi ko'radi.
    PATCH - FAQAT manager (director endi menu_background'ni O'ZGARTIRA
    OLMAYDI, faqat ko'radi - qarang: apps.permission.IsRestaurantManagerOnly).

    Create uchun: slug yuborilmasa yoki bo'sh bo'lsa, `name`dan avtomatik
    slugify qilinadi; bazada mavjud bo'lsa oxiriga raqam qo'shiladi.
    """

    slug = CharField(required=False, allow_blank=True)

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "menu_background",
            "owner",
            "created_at",
        )

        read_only_fields = (
            "id",
            "is_active",
            "owner",
            "created_at",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        name = attrs.get("name") or getattr(self.instance, "name", "")
        raw_slug = (attrs.get("slug") or "").strip()
        if self.instance is None:
            # create
            attrs["slug"] = unique_restaurant_slug(name, preferred=raw_slug or None)
        elif "slug" in attrs:
            # update: faqat yuborilgan non-empty slugni qabul qilamiz
            if raw_slug:
                attrs["slug"] = unique_restaurant_slug(
                    name, preferred=raw_slug, exclude_pk=self.instance.pk
                )
            else:
                attrs.pop("slug", None)
        return attrs

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = unique_restaurant_slug(validated_data["name"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        role = getattr(request.user, "role", None) if request else None
        if role != User.Role.MANAGER:
            validated_data.pop("menu_background", None)
        # Oddiy /restaurant/me/ PATCH da slug o'zgarmasligi kerak
        validated_data.pop("slug", None)
        return super().update(instance, validated_data)


class SuperAdminRestaurantSerializer(ModelSerializer):
    """
    Super Admin dashboard uchun kengaytirilgan serializer: obuna holati bilan birga.
    Ro'yxatda "nechta restoran, obunasi faolmi, muddati qachon tugaydi" ko'rsatish uchun.

    TUZATISH: obuna endi bitta reja bo'lgani uchun `plan_type` olib tashlandi,
    o'rniga `subscription_price` va `has_active_subscription` qo'shildi.
    `manager_phone` -> `director_phone`ga o'zgartirildi (restoran egasi endi
    director roli, `Restaurant.owner`).
    """

    director_phone = SerializerMethodField()
    subscription_price = SerializerMethodField()
    subscription_days_remaining = SerializerMethodField()
    subscription_end_date = SerializerMethodField()
    has_active_subscription = SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "owner",
            "director_phone",
            "subscription_price",
            "subscription_days_remaining",
            "subscription_end_date",
            "has_active_subscription",
            "created_at",
        )
        read_only_fields = fields

    def _get_subscription(self, obj: Restaurant) -> Subscription | None:
        return getattr(obj, "subscription_info", None)

    def get_subscription_price(self, obj: Restaurant):
        sub = self._get_subscription(obj)
        return sub.price if sub else None

    def get_subscription_days_remaining(self, obj: Restaurant):
        sub = self._get_subscription(obj)
        return sub.days_remaining if sub else None

    def get_subscription_end_date(self, obj: Restaurant):
        sub = self._get_subscription(obj)
        return sub.end_date if sub else None

    def get_has_active_subscription(self, obj: Restaurant):
        sub = self._get_subscription(obj)
        return sub.has_access if sub else False

    def get_director_phone(self, obj: Restaurant):
        return obj.owner.phone if obj.owner_id else None


class TableSerializer(ModelSerializer):
    class Meta:
        model = Table
        fields = "id", "restaurant", "number", "qr_hash", "is_active"
        read_only_fields = "id", "restaurant", "qr_hash"


class DishSerializer(ModelSerializer):
    """
    Director/Manager uchun taom serializeri (yaratish/tahrirlash/o'chirish).

    Tekshiruv `user.restaurant_id` asosida - bu barcha rollar uchun to'g'ri ishlaydi.

    Taom qo'shish/tahrirlash huquqi FAQAT manager uchun (director EMAS) - bu
    view/permission qatlamida (IsRestaurantManagerOnly) cheklanadi;
    oshpaz (chef) bu serializer orqali umuman yozish so'rovi yubora olmasligi kerak
    (faqat GET/read-only).
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
            "requires_kitchen",
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
