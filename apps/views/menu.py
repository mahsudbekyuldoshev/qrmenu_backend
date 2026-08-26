from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models.notifications import WaiterCall
from apps.models.orders import Order, OrderItem
from apps.models.restaurants import Category, Dish, Table
from apps.permission import IsRestaurantStaff
from apps.serializers.menu import PublicCategorySerializer, PublicRestaurantSerializer
from apps.serializers.notifications import WaiterCallSerializer

QR_HASH_PARAM = OpenApiParameter(
    name="qr_hash",
    type=str,
    location=OpenApiParameter.PATH,
    description="Stolga tegishli QR-kod hash'i.",
)


@extend_schema(tags=["Public Menu"])
class PublicMenuView(APIView):
    """Mijoz uchun ochiq menyu. Auth kerak emas - stol QR-hash orqali kiriladi."""

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[QR_HASH_PARAM],
        responses={200: OpenApiResponse(description="Restoran va menyu ma'lumotlari.")},
    )
    def get(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        categories = Category.objects.filter(
            restaurant=table.restaurant, is_active=True
        ).prefetch_related("dishes")

        return Response(
            {
                "restaurant": PublicRestaurantSerializer(
                    table.restaurant, context={"request": request}
                ).data,
                "restaurant_name": table.restaurant.name,
                "table_number": table.number,
                "table_id": table.id,
                "categories": PublicCategorySerializer(categories, many=True).data,
            }
        )


@extend_schema(tags=["Public Menu"])
class PublicOrderCreateView(APIView):
    """Mijoz stol orqali buyurtma beradi. Auth kerak emas."""

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[QR_HASH_PARAM],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dish": {"type": "integer"},
                                "quantity": {"type": "integer", "default": 1},
                            },
                        },
                    }
                },
            }
        },
        responses={
            201: OpenApiResponse(description="Yaratilgan buyurtma id va summasi."),
            400: OpenApiResponse(description="Taom tanlanmagan yoki mavjud emas."),
        },
        examples=[
            OpenApiExample(
                "Buyurtma so'rovi",
                value={"items": [{"dish": 1, "quantity": 2}, {"dish": 5, "quantity": 1}]},
                request_only=True,
            ),
        ],
    )
    def post(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        items_data = request.data.get("items", [])

        if not items_data:
            return Response({"items": "Kamida bitta taom tanlanishi shart."}, status=400)

        order = Order.objects.create(restaurant=table.restaurant, table=table)
        total = 0
        for item_data in items_data:
            dish_id = item_data.get("dish")
            quantity = item_data.get("quantity", 1)
            try:
                dish = Dish.objects.get(
                    id=dish_id, category__restaurant=table.restaurant, is_available=True
                )
            except Dish.DoesNotExist:
                order.delete()
                return Response(
                    {"items": f"ID={dish_id} bo'lgan taom mavjud emas yoki tugagan."}, status=400
                )
            # OrderItem.save() ichida dish.requires_kitchen'ga qarab boshlang'ich
            # status avtomatik belgilanadi (kitchen kerak bo'lmasa - darhol "ready").
            item = OrderItem.objects.create(order=order, dish=dish, quantity=quantity, price=dish.price)
            total += item.price * item.quantity

        order.total_price = total
        order.save(update_fields=["total_price"])
        order.refresh_status()
        return Response({"order_id": order.id, "total_price": str(order.total_price)}, status=201)


@extend_schema(tags=["Public Menu"])
class CallWaiterView(APIView):
    """
    POST /menu/{qr_hash}/call-waiter/
    Mijoz "Ofitsiant" tugmasini bosganda - oddiy xizmat chaqiruvi
    (qo'shimcha buyurtma, salfetka va h.k. - sabab ko'rsatilmasligi ham
    mumkin, ofitsiant stolga borib so'raydi).
    """

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[QR_HASH_PARAM],
        request=None,
        responses={201: WaiterCallSerializer},
    )
    def post(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        call = WaiterCall.objects.create(
            restaurant=table.restaurant, table=table, call_type=WaiterCall.CallType.SERVICE
        )
        return Response(WaiterCallSerializer(call).data, status=201)


@extend_schema(tags=["Public Menu"])
class RequestPaymentView(APIView):
    """
    POST /menu/{qr_hash}/request-payment/  body: {"order_id": 123}
    Mijoz "To'lov" tugmasini bosganda - ofitsiantga stol raqami va
    to'lanadigan summa bilan birga bildirishnoma yuboriladi.
    """

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[QR_HASH_PARAM],
        request={
            "application/json": {
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            }
        },
        responses={201: WaiterCallSerializer},
    )
    def post(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        order_id = request.data.get("order_id")
        order = get_object_or_404(Order, id=order_id, restaurant=table.restaurant, table=table)

        call = WaiterCall.objects.create(
            restaurant=table.restaurant,
            table=table,
            order=order,
            call_type=WaiterCall.CallType.PAYMENT,
            amount=order.total_price,
        )
        return Response(WaiterCallSerializer(call).data, status=201)


@extend_schema(tags=["Staff / Waiter Calls"])
class WaiterCallResolveView(APIView):
    """
    PATCH /waiter-calls/{id}/resolve/
    Ofitsiant chaqiruvni ko'rib, bajargandan keyin shu orqali yopadi.
    """

    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    @extend_schema(
        request=None,
        responses={200: WaiterCallSerializer},
    )
    def patch(self, request, pk):
        from django.utils import timezone

        call = get_object_or_404(WaiterCall, pk=pk, restaurant=request.user.restaurant)
        call.status = WaiterCall.Status.RESOLVED
        call.resolved_at = timezone.now()
        call.save(update_fields=["status", "resolved_at"])
        return Response(WaiterCallSerializer(call).data)