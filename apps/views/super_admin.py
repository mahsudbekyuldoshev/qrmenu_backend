from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.models.restaurants import Restaurant
from apps.models.subscriptions import Payment
from apps.models.users import User
from apps.permission import IsSuperAdmin
from apps.serializers.super_admin import (
    AdminDashboardSerializer,
    AssignDirectorSerializer,
    DirectorCreateSerializer,
    DirectorSerializer,
    PaymentSerializer,
    RenewSubscriptionSerializer,
    RestaurantAdminCreateSerializer,
    RestaurantAdminDetailSerializer,
)


class DirectorViewSet(ModelViewSet):
    """
    Super Admin - direktor hisoblarini yaratadi/ko'radi/tahrirlaydi/o'chiradi.
    Yaratishda `DirectorCreateSerializer` (parol bilan), boshqa amallarda
    `DirectorSerializer` (parolsiz) ishlatiladi.
    """

    permission_classes = (IsAuthenticated, IsSuperAdmin)
    queryset = User.objects.filter(role=User.Role.DIRECTOR).select_related("restaurant")

    def get_serializer_class(self):
        if self.action == "create":
            return DirectorCreateSerializer
        return DirectorSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        director = serializer.save()

        response_data = DirectorSerializer(director).data
        generated = getattr(director, "_generated_password", None)
        if generated:
            response_data["generated_password"] = generated
        return Response(response_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        director = self.get_object()
        restaurant = director.restaurant
        # Direktor o'chirilsa, restoran "egasiz" qolmasin - owner bog'lanishini tozalaymiz.
        if restaurant and restaurant.owner_id == director.id:
            restaurant.owner = None
            restaurant.save(update_fields=["owner"])
        return super().destroy(request, *args, **kwargs)


class RestaurantAdminViewSet(ModelViewSet):
    """
    Super Admin - restoranlarni yaratadi/ko'radi/tahrirlaydi/o'chiradi,
    direktor biriktiradi, obunani uzaytiradi.
    """

    permission_classes = (IsAuthenticated, IsSuperAdmin)
    queryset = Restaurant.objects.select_related(
        "owner", "subscription_info"
    ).prefetch_related("staff")

    def get_serializer_class(self):
        if self.action == "create":
            return RestaurantAdminCreateSerializer
        return RestaurantAdminDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.save()
        return Response(
            RestaurantAdminDetailSerializer(restaurant).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="assign-director")
    def assign_director(self, request, pk=None):
        """POST /admin/restaurants/{id}/assign-director/  body: {"director_id": N}"""
        restaurant = self.get_object()
        serializer = AssignDirectorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(restaurant=restaurant)
        return Response(RestaurantAdminDetailSerializer(restaurant).data)

    @action(detail=True, methods=["post"], url_path="renew-subscription")
    def renew_subscription(self, request, pk=None):
        """
        POST /admin/restaurants/{id}/renew-subscription/
        body: {"amount": 299000, "months": 1, "note": "Naqd to'lov"}
        Har chaqiriqda `Payment` yozuvi yaratiladi va obuna muddati uzayadi.
        """
        restaurant = self.get_object()
        subscription = getattr(restaurant, "subscription_info", None)
        if subscription is None:
            return Response(
                {"detail": "Bu restoranda obuna topilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RenewSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(subscription=subscription)

        return Response(
            {
                "restaurant": RestaurantAdminDetailSerializer(restaurant).data,
                "payment": PaymentSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="payments")
    def payments(self, request, pk=None):
        """GET /admin/restaurants/{id}/payments/ - to'lovlar tarixi."""
        restaurant = self.get_object()
        subscription = getattr(restaurant, "subscription_info", None)
        if subscription is None:
            return Response([])
        return Response(
            PaymentSerializer(subscription.payments.all(), many=True).data
        )


class AdminDashboardView(APIView):
    """
    GET /admin/dashboard/
    Super Admin bosh sahifasi: jami restoranlar/direktorlar soni, har bir
    restoran uchun obuna holati, to'langan summa va xodimlar soni.
    """

    permission_classes = (IsAuthenticated, IsSuperAdmin)

    def get(self, request):
        restaurants = Restaurant.objects.select_related(
            "owner", "subscription_info"
        ).prefetch_related("staff")

        total_restaurants = restaurants.count()
        total_directors = User.objects.filter(role=User.Role.DIRECTOR).count()

        active_subscriptions = sum(
            1
            for r in restaurants
            if getattr(r, "subscription_info", None) and r.subscription_info.has_access
        )
        expired_subscriptions = total_restaurants - active_subscriptions

        data = {
            "total_restaurants": total_restaurants,
            "total_directors": total_directors,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "restaurants": restaurants,
        }
        return Response(AdminDashboardSerializer(data).data)


class AdminAnalyticsView(APIView):
    """
    GET /admin/analytics/?period=daily|weekly|monthly (default: monthly)

    Super Admin uchun grafik ma'lumotlari:
    - restaurants_over_time: tanlangan davr bo'yicha necha restoran qo'shilgani
    - revenue_over_time: oylar bo'yicha yig'ilgan to'lovlar summasi
    - total_revenue: hozirgacha yig'ilgan JAMI to'lov
    - subscription_status: faol/tugagan obunalar soni VA foizi
    """

    permission_classes = (IsAuthenticated, IsSuperAdmin)

    TRUNC_MAP = {"daily": TruncDate, "weekly": TruncWeek, "monthly": TruncMonth}

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        trunc_fn = self.TRUNC_MAP.get(period, TruncMonth)

        # --- Restoranlar vaqt bo'yicha (oxirgi 12 nuqta) ---
        restaurants_qs = (
            Restaurant.objects.annotate(bucket=trunc_fn("created_at"))
            .values("bucket")
            .annotate(count=Count("id"))
            .order_by("bucket")
        )
        restaurants_over_time = [
            {"date": row["bucket"], "count": row["count"]} for row in restaurants_qs
        ]

        # --- Oylik tushum (oxirgi 12 oy, bo'sh oylar 0 bilan to'ldiriladi) ---
        revenue_qs = (
            Payment.objects.annotate(bucket=TruncMonth("paid_at"))
            .values("bucket")
            .annotate(total=Sum("amount"))
            .order_by("bucket")
        )
        revenue_map = {
            row["bucket"].date().replace(day=1) if hasattr(row["bucket"], "date") else row["bucket"]: row["total"]
            for row in revenue_qs
            if row["bucket"]
        }

        now = timezone.now()
        revenue_over_time = []
        for i in range(11, -1, -1):
            # i oy oldin
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            bucket = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone()).date()
            # match keys that may be datetime or date
            total = Decimal("0")
            for k, v in revenue_map.items():
                kd = k.date() if hasattr(k, "date") else k
                if kd.year == year and kd.month == month:
                    total = v or Decimal("0")
                    break
            revenue_over_time.append({"month": f"{year}-{month:02d}-01", "total": total})

        total_revenue = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0

        # --- Obuna holati (faol/tugagan), foizda ---
        restaurants = Restaurant.objects.select_related("subscription_info")
        total_restaurants = restaurants.count()
        active_count = sum(
            1
            for r in restaurants
            if getattr(r, "subscription_info", None) and r.subscription_info.has_access
        )
        expired_count = total_restaurants - active_count
        active_percent = round((active_count / total_restaurants * 100), 1) if total_restaurants else 0
        expired_percent = round((expired_count / total_restaurants * 100), 1) if total_restaurants else 0

        return Response(
            {
                "restaurants_over_time": restaurants_over_time,
                "revenue_over_time": revenue_over_time,
                "total_revenue": total_revenue,
                "subscription_status": {
                    "active_count": active_count,
                    "active_percent": active_percent,
                    "expired_count": expired_count,
                    "expired_percent": expired_percent,
                    "total_restaurants": total_restaurants,
                },
            }
        )