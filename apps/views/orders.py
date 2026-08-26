from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.models.notifications import WaiterCall
from apps.models.orders import Order, OrderItem
from apps.permission import IsRestaurantStaff
from apps.serializers.notifications import WaiterCallSerializer
from apps.serializers.orders import (
    OrderItemSerializer,
    OrderItemStatusUpdateSerializer,
    OrderSerializer,
)

# Rolga qarab RUXSAT ETILGAN status o'tishlari. Kalit - (rol, hozirgi_status),
# qiymat - shu holatdan o'tish mumkin bo'lgan status'lar to'plami.
ALLOWED_TRANSITIONS = {
    "chef": {
        OrderItem.Status.PENDING: {OrderItem.Status.PREPARING, OrderItem.Status.READY},
        OrderItem.Status.PREPARING: {OrderItem.Status.READY},
    },
    "waiter": {
        OrderItem.Status.READY: {OrderItem.Status.DELIVERED},
    },
    # director/manager - nazorat uchun istalgan holatga o'tkaza oladi.
    "director": "ANY",
    "manager": "ANY",
}


@extend_schema_view(
    list=extend_schema(
        tags=["Orders"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Vergul bilan ajratilgan status'lar bo'yicha filtr (masalan: pending,preparing).",
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Orders"]),
    create=extend_schema(tags=["Orders"]),
    update=extend_schema(tags=["Orders"]),
    partial_update=extend_schema(tags=["Orders"]),
    destroy=extend_schema(tags=["Orders"]),
)
class OrderViewSet(ModelViewSet):
    """
    Buyurtmalar - manager/director/waiter/chef uchun ochiq (IsRestaurantStaff).
    Real vaqtdagi KDS/Waiter navbatlari uchun pastdagi maxsus
    KitchenQueueView/WaiterQueueView'dan foydalaning - bu ViewSet asosan
    umumiy ro'yxat/tarix ko'rish uchun.
    """

    serializer_class = OrderSerializer
    permission_classes = IsAuthenticated, IsRestaurantStaff

    def get_queryset(self):
        queryset = (
            Order.objects.filter(restaurant=self.request.user.restaurant)
            .select_related("restaurant", "table")
            .prefetch_related("items", "items__dish")
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            queryset = queryset.filter(status__in=statuses)
        return queryset

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


@extend_schema(tags=["Staff / Kitchen"])
class KitchenQueueView(APIView):
    """
    GET /kitchen/queue/
    Oshpaz (KDS) ekrani uchun: `dish.requires_kitchen=True` bo'lgan va
    hali yetkazilmagan (PENDING/PREPARING) itemlar ro'yxati, eng eski
    birinchi (FIFO).

    Bu RESTORANGA umumiy navbat - bitta restorandagi barcha oshpazlar
    BIR XIL ro'yxatni ko'radi (har biriga alohida shaxsiy navbat emas).
    """

    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    @extend_schema(responses=OrderItemSerializer(many=True))
    def get(self, request):
        items = (
            OrderItem.objects.filter(
                order__restaurant=request.user.restaurant,
                dish__requires_kitchen=True,
                status__in=[OrderItem.Status.PENDING, OrderItem.Status.PREPARING],
            )
            .select_related("dish", "order", "order__table")
            .order_by("created_at")
        )
        return Response(OrderItemSerializer(items, many=True).data)


@extend_schema(tags=["Staff / Waiter"])
class WaiterQueueView(APIView):
    """
    GET /waiter/queue/
    Ofitsiant (Waiter Station) ekrani uchun: yetkazishga TAYYOR itemlar
    (kelib chiqishidan qat'i nazar - oshxonadan kelgan ham, to'g'ridan-to'g'ri
    tushgan non/suv ham) + hal qilinmagan chaqiruvlar (WaiterCall: xizmat/
    to'lov so'rovi).

    Bu ham RESTORANGA umumiy navbat - barcha ofitsiantlar bir xil ro'yxatni
    ko'radi.
    """

    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Tayyor itemlar va hal qilinmagan chaqiruvlar ro'yxati.",
            )
        }
    )
    def get(self, request):
        ready_items = (
            OrderItem.objects.filter(
                order__restaurant=request.user.restaurant,
                status=OrderItem.Status.READY,
            )
            .select_related("dish", "order", "order__table")
            .order_by("created_at")
        )
        pending_calls = WaiterCall.objects.filter(
            restaurant=request.user.restaurant, status=WaiterCall.Status.PENDING
        ).select_related("table").order_by("created_at")

        return Response(
            {
                "ready_items": OrderItemSerializer(ready_items, many=True).data,
                "calls": WaiterCallSerializer(pending_calls, many=True).data,
            }
        )


@extend_schema(tags=["Orders"])
class OrderItemStatusUpdateView(APIView):
    """
    PATCH /order-items/{id}/status/  body: {"status": "ready"}

    Rolga qarab qat'iy tekshiriladi (ALLOWED_TRANSITIONS):
    - chef: faqat oshxona taomlarini pending/preparing -> ready qila oladi
    - waiter: faqat ready -> delivered qila oladi (har qanday item uchun)
    - director/manager: nazorat maqsadida istalgan o'tishni qila oladi

    Har bir muvaffaqiyatli yangilanishdan keyin Order.status ham avtomatik
    qayta hisoblanadi (`order.refresh_status()`).
    """

    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    @extend_schema(
        request=OrderItemStatusUpdateSerializer,
        responses={
            200: OrderItemSerializer,
            403: OpenApiResponse(description="Rolingiz uchun bu status o'tishi ruxsat etilmagan."),
        },
    )
    def patch(self, request, pk):
        item = get_object_or_404(
            OrderItem, pk=pk, order__restaurant=request.user.restaurant
        )
        serializer = OrderItemStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        role = request.user.role
        rule = ALLOWED_TRANSITIONS.get(role)
        if rule is None:
            raise PermissionDenied("Sizning rolingiz buyurtma holatini o'zgartira olmaydi.")
        if rule != "ANY" and new_status not in rule.get(item.status, set()):
            raise PermissionDenied(
                f"'{item.get_status_display()}' holatidan "
                f"'{OrderItem.Status(new_status).label}'ga o'tish sizning "
                f"rolingiz uchun ruxsat etilmagan."
            )

        item.status = new_status
        item.save(update_fields=["status"])
        item.order.refresh_status()

        return Response(OrderItemSerializer(item).data)