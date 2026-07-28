from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models.orders import Order, OrderItem
from apps.models.restaurants import Category, Dish, Table
from apps.serializers.menu import PublicCategorySerializer


class PublicMenuView(APIView):
    """
    Mijoz uchun ochiq menyu. Auth kerak emas — faqat stol QR-hash orqali kiriladi.
    Bu APIView bo'lishi kerak, ViewSet emas: bu yerda faqat bitta GET amali bor
    (menyuni ko'rish), na list, na create, na delete kerak emas.
    """
    permission_classes = AllowAny

    def get(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        categories = Category.objects.filter(
            restaurant=table.restaurant, is_active=True
        ).prefetch_related("dishes")

        return Response(
            {
                "restaurant_name": table.restaurant.name,
                "table_number": table.number,
                "categories": PublicCategorySerializer(categories, many=True).data,
            }
        )


class PublicOrderCreateView(APIView):
    """
    Mijoz stol orqali buyurtma beradi. Auth kerak emas.

    Bu ham APIView bo'lishi kerak: mijozga faqat POST (yaratish) kerak — u o'z
    buyurtmasini ko'ra olmaydi/o'zgartira olmaydi (bu xodimning OrderViewSet ishi).
    """

    permission_classes = AllowAny

    def post(self, request, qr_hash):
        table = get_object_or_404(Table, qr_hash=qr_hash, is_active=True)
        items_data = request.data.get("items", [])

        if not items_data:
            return Response(
                {"items": "Kamida bitta taom tanlanishi shart."}, status=400
            )

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
                    {"items": f"ID={dish_id} bo'lgan taom mavjud emas yoki tugagan."},
                    status=400,
                )
            item = OrderItem.objects.create(
                order=order, dish=dish, quantity=quantity, price=dish.price
            )
            total += item.price * item.quantity

        order.total_price = total
        order.save()
        return Response(
            {"order_id": order.id, "total_price": str(order.total_price)}, status=201
        )
