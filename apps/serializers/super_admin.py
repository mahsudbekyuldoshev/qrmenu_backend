import calendar
from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    DecimalField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models.manager.user_manager import UserManager
from apps.models.restaurants import Restaurant
from apps.models.subscriptions import Payment, Subscription
from apps.models.users import User
from apps.serializers.staff import generate_random_password
from apps.utils.slugs import unique_restaurant_slug


def add_months(dt, months: int):
    """
    `dt` sanasiga `months` oy qo'shadi (tashqi kutubxonasiz, `python-dateutil`
    o'rniga). Oy oxiridagi kunlar sonini hisobga oladi (masalan 31-yanvar +
    1 oy = 28/29-fevral).
    """
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


# ---------------------------------------------------------------------------
# DIREKTOR
# ---------------------------------------------------------------------------

class DirectorCreateSerializer(Serializer):
    """
    Super Admin yangi direktor hisobini yaratadi. Bosqich 1: hali restoranga
    bog'lanmagan - keyin `RestaurantAdminViewSet.assign_director` orqali
    biror restoranga biriktiriladi.

    `must_change_password=True` bilan yaratiladi - direktor birinchi
    kirganda albatta o'z parolini o'zgartirishi shart (/auth/change-password/).
    """

    phone = CharField(max_length=20)
    password = CharField(min_length=8, write_only=True, required=False, allow_blank=True)
    first_name = CharField(max_length=150, required=False, allow_blank=True)
    last_name = CharField(max_length=150, required=False, allow_blank=True)

    def validate_phone(self, value):
        phone = UserManager.normalize_phone(value)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon roʻyxatdan oʻtgan.")
        return phone

    def create(self, validated_data):
        password = validated_data.get("password") or generate_random_password(12)
        director = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.DIRECTOR,
            must_change_password=True,
        )
        director._generated_password = None if validated_data.get("password") else password
        return director


class DirectorSerializer(ModelSerializer):
    """Direktorlar ro'yxati/detali/tahrirlash uchun (parolsiz)."""

    restaurant_id = SerializerMethodField()
    restaurant_name = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "first_name",
            "last_name",
            "is_active",
            "employment_status",
            "must_change_password",
            "restaurant_id",
            "restaurant_name",
        )
        read_only_fields = ("id", "phone", "restaurant_id", "restaurant_name", "must_change_password")

    def get_restaurant_id(self, obj: User):
        return obj.restaurant_id

    def get_restaurant_name(self, obj: User):
        return obj.restaurant.name if obj.restaurant_id else None

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if "employment_status" in validated_data:
            instance.is_active = instance.employment_status == User.EmploymentStatus.WORKING
            instance.save(update_fields=["is_active"])
        return instance


# ---------------------------------------------------------------------------
# OBUNA / TO'LOV
# ---------------------------------------------------------------------------

class SubscriptionInlineSerializer(Serializer):
    """Restoran yaratishda birga kiritiladigan boshlang'ich obuna ma'lumoti."""

    price = DecimalField(max_digits=12, decimal_places=2, required=False)
    months = IntegerField(min_value=1, required=False, default=1)


class RenewSubscriptionSerializer(Serializer):
    """
    Obunani uzaytirish/to'lov qabul qilish uchun.
    Har chaqiriqda bitta `Payment` yozuvi yaratiladi va `end_date` shu
    muddatga (yoki hozirgi sanadan, agar muddati allaqachon tugagan bo'lsa)
    suriladi.
    """

    amount = DecimalField(max_digits=12, decimal_places=2)
    months = IntegerField(min_value=1, default=1)
    note = CharField(max_length=255, required=False, allow_blank=True)

    def save(self, subscription: Subscription) -> Payment:
        months = self.validated_data["months"]
        base = subscription.end_date if not subscription.is_expired else timezone.now()
        subscription.end_date = add_months(base, months)
        subscription.is_active = True
        subscription.save(update_fields=["end_date", "is_active"])

        return Payment.objects.create(
            subscription=subscription,
            amount=self.validated_data["amount"],
            period_months=Decimal(months),
            note=self.validated_data.get("note", ""),
        )


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = "id", "amount", "period_months", "note", "paid_at"
        read_only_fields = fields


# ---------------------------------------------------------------------------
# RESTORAN
# ---------------------------------------------------------------------------

class RestaurantAdminCreateSerializer(ModelSerializer):
    """
    Super Admin yangi restoran yaratadi. `subscription` ichma-ich obyekt
    sifatida beriladi (price/months ixtiyoriy - berilmasa default narx va
    1 oylik muddat qo'llanadi). Direktor bu bosqichda bog'lanmaydi - alohida
    `assign_director` action orqali biriktiriladi.

    `slug` ixtiyoriy: kelmasa yoki bo'sh bo'lsa `name`dan avtomatik generatsiya.
    """

    slug = CharField(required=False, allow_blank=True)
    subscription = SubscriptionInlineSerializer(write_only=True, required=False)

    class Meta:
        model = Restaurant
        fields = ("id", "name", "slug", "is_active", "subscription")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        name = attrs.get("name", "")
        raw_slug = (attrs.get("slug") or "").strip()
        attrs["slug"] = unique_restaurant_slug(name, preferred=raw_slug or None)
        return attrs

    def create(self, validated_data):
        sub_data = validated_data.pop("subscription", {})
        restaurant = Restaurant.objects.create(**validated_data)

        price = sub_data.get("price") or Subscription._meta.get_field("price").default
        months = sub_data.get("months", 1)
        Subscription.objects.create(
            restaurant=restaurant,
            price=price,
            end_date=add_months(timezone.now(), months),
        )
        return restaurant


class AssignDirectorSerializer(Serializer):
    """
    Direktorni restoranga bog'laydi.
    Bir direktor bir nechta restoranga `owner` bo'lishi mumkin;
    `User.restaurant` faqat birinchi (asosiy) restoran sifatida saqlanadi.
    """

    director_id = IntegerField()

    def validate_director_id(self, value):
        try:
            return User.objects.get(id=value, role=User.Role.DIRECTOR)
        except User.DoesNotExist:
            raise ValidationError("Bunday direktor topilmadi.")

    def save(self, restaurant: Restaurant):
        director = self.validated_data["director_id"]
        if not director.restaurant_id:
            director.restaurant = restaurant
            director.save(update_fields=["restaurant"])
        restaurant.owner = director
        restaurant.save(update_fields=["owner"])
        return restaurant


class RestaurantAdminDetailSerializer(ModelSerializer):
    """
    Super Admin dashboard ro'yxati/detali uchun to'liq ma'lumot: direktor,
    obuna holati (necha kun qoldi, jami to'langan summa) va xodimlar soni.
    """

    director = DirectorSerializer(source="owner", read_only=True)
    subscription_price = SerializerMethodField()
    subscription_days_remaining = SerializerMethodField()
    subscription_end_date = SerializerMethodField()
    has_active_subscription = SerializerMethodField()
    total_paid = SerializerMethodField()
    staff_count = SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "director",
            "subscription_price",
            "subscription_days_remaining",
            "subscription_end_date",
            "has_active_subscription",
            "total_paid",
            "staff_count",
            "created_at",
        )
        read_only_fields = fields

    def _sub(self, obj: Restaurant) -> Subscription | None:
        return getattr(obj, "subscription_info", None)

    def get_subscription_price(self, obj):
        sub = self._sub(obj)
        return sub.price if sub else None

    def get_subscription_days_remaining(self, obj):
        sub = self._sub(obj)
        return sub.days_remaining if sub else None

    def get_subscription_end_date(self, obj):
        sub = self._sub(obj)
        return sub.end_date if sub else None

    def get_has_active_subscription(self, obj):
        sub = self._sub(obj)
        return sub.has_access if sub else False

    def get_total_paid(self, obj):
        sub = self._sub(obj)
        return sub.total_paid if sub else Decimal("0")

    def get_staff_count(self, obj):
        # director + manager + waiter + chef - hammasi shu restoranga
        # `restaurant_id` orqali bog'langan (director ham shu FK orqali).
        return obj.staff.count()


class AdminDashboardSerializer(Serializer):
    """Super Admin bosh sahifasi uchun umumiy statistika."""

    total_restaurants = IntegerField()
    total_directors = IntegerField()
    active_subscriptions = IntegerField()
    expired_subscriptions = IntegerField()
    restaurants = RestaurantAdminDetailSerializer(many=True)