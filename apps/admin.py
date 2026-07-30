from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Restaurant, Subscription, User
from apps.permission import IsSuperAdmin
from apps.serializers.restaurants import SuperAdminRestaurantSerializer


class SuperAdminRestaurantListView(ListAPIView):
    """
    Super Admin dashboard - platformadagi barcha restoranlar ro'yxati:
    nomi, manager telefoni, obuna turi (trial/paid), qolgan kunlar soni.
    """

    serializer_class = SuperAdminRestaurantSerializer
    permission_classes = (IsAuthenticated, IsSuperAdmin)
    queryset = Restaurant.objects.select_related(
        "owner", "subscription_info"
    ).order_by("-created_at")


class CreateRestaurantWithManagerSerializer(serializers.Serializer):
    """
    Super Admin bitta so'rov bilan: yangi restoran + unga biriktirilgan manager
    hisobini + boshlang'ich obunani (trial yoki paid) yaratadi.
    """

    restaurant_name = serializers.CharField(max_length=255)
    manager_phone = serializers.CharField(max_length=20)
    manager_password = serializers.CharField(min_length=8, write_only=True)
    manager_full_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    plan_type = serializers.ChoiceField(
        choices=Subscription.PlanType.choices, default=Subscription.PlanType.TRIAL
    )
    trial_days = serializers.IntegerField(default=14, min_value=1)

    def validate_manager_phone(self, value):
        from apps.models.manager.user_manager import UserManager

        phone = UserManager.normalize_phone(value)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return phone

    def create(self, validated_data):
        from django.utils.text import slugify

        restaurant_name = validated_data["restaurant_name"].strip()
        base_slug = slugify(restaurant_name) or "restaurant"
        slug = base_slug
        i = 1
        while Restaurant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{i}"
            i += 1

        restaurant = Restaurant.objects.create(
            name=restaurant_name, slug=slug, is_active=True
        )

        full_name = validated_data.get("manager_full_name", "").strip()
        first_name, _, last_name = full_name.partition(" ")

        manager = User.objects.create_user(
            phone=validated_data["manager_phone"],
            password=validated_data["manager_password"],
            first_name=first_name,
            last_name=last_name,
            role=User.Role.MANAGER,
            restaurant=restaurant,
        )
        restaurant.owner = manager
        restaurant.save(update_fields=["owner"])

        Subscription.objects.create(
            restaurant=restaurant,
            plan_name=validated_data["plan_type"].capitalize(),
            plan_type=validated_data["plan_type"],
            is_active=True,
            end_date=timezone.now()
            + timezone.timedelta(days=validated_data["trial_days"]),
        )

        return restaurant


class SuperAdminCreateRestaurantView(CreateAPIView):
    """
    POST: yangi restoran yaratish + unga manager biriktirish + obuna ochish.
    Faqat Super Admin foydalana oladi.
    """

    serializer_class = CreateRestaurantWithManagerSerializer
    permission_classes = (IsAuthenticated, IsSuperAdmin)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.save()
        return Response(
            SuperAdminRestaurantSerializer(restaurant).data,
            status=status.HTTP_201_CREATED,
        )


class SuperAdminRestaurantDetailView(APIView):
    """
    PATCH: restoran holatini o'zgartirish (is_active) yoki obunasini yangilash
    (masalan trial muddatini uzaytirish, paid'ga o'tkazish).
    """

    permission_classes = (IsAuthenticated, IsSuperAdmin)

    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404

        restaurant = get_object_or_404(Restaurant, pk=pk)

        if "is_active" in request.data:
            restaurant.is_active = bool(request.data["is_active"])
            restaurant.save(update_fields=["is_active"])

        sub = getattr(restaurant, "subscription_info", None)
        if sub:
            if "plan_type" in request.data:
                sub.plan_type = request.data["plan_type"]
            if "extend_days" in request.data:
                sub.end_date = timezone.now() + timezone.timedelta(
                    days=int(request.data["extend_days"])
                )
            sub.save()

        return Response(SuperAdminRestaurantSerializer(restaurant).data)