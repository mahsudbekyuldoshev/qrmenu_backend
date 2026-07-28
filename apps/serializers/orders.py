from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, JSONField, ReadOnlyField
from rest_framework.serializers import ModelSerializer

from apps.models.orders import Order, OrderItem
from apps.models.restaurants import Dish


class OrderItemSerializer(ModelSerializer):
    """
    Buyurtma tarkibidagi taomlar serializeri.
    """
    dish_name = ReadOnlyField(source="dish.name")
    class Meta:
        model = OrderItem
        fields = "id", "order", "dish", "dish_name", "quantity", "price"
        read_only_fields = "id", "price"


class OrderSerializer(ModelSerializer):
    """
    Buyurtma serializeri (xodimlar/staff uchun — OrderViewSet orqali ishlatiladi).
    Mijozning QR orqali ochiq buyurtma berishi uchun bu serializer ISHLATILMAYDI —
    u alohida apps/views/menu.py:PublicOrderCreateView'da oddiy dict bilan ishlanadi,
    chunki u yerda auth yo'q va restaurant/table token orqali aniqlanadi.
    """

    items = OrderItemSerializer(many=True, read_only=True)
    uploaded_items = JSONField(write_only=True, required=True)

    status_display = CharField(source="get_status_display", read_only=True)
    restaurant_name = ReadOnlyField(source="restaurant.name")
    table_number = ReadOnlyField(source="table.number")

    class Meta:
        model = Order
        fields = (
            "id",
            "restaurant",
            "restaurant_name",
            "table",
            "table_number",
            "status",
            "status_display",
            "total_price",
            "comment",
            "items",
            "uploaded_items",
            "created_at",
        )
        read_only_fields = "id", "restaurant", "total_price", "created_at"

    def validate_uploaded_items(self, value):
        if not value:
            raise ValidationError("Kamida bitta taom kiritilishi shart.")
        for item in value:
            if "dish" not in item:
                raise ValidationError("Har bir item uchun 'dish' maydoni majburiy.")
            quantity = item.get("quantity", 1)
            if not isinstance(quantity, int) or quantity < 1:
                raise ValidationError("'quantity' musbat butun son bo'lishi kerak.")
        return value

    def validate_table(self, value):
        # TUZATISH: stol boshqa restoranga tegishli bo'lmasligini tekshiradi.
        request = self.context.get("request")
        if request and value and value.restaurant.owner_id != request.user.id:
            raise ValidationError("Bu stol sizning restoraningizga tegishli emas.")
        return value

    def create(self, validated_data):
        """
        Nested itemlar bilan buyurtmani yaratish.
        TUZATISH: avval noto'g'ri dish ID kelsa xato "yutib yuborilardi" (silent failure) va
        yaroqsiz/yarim buyurtma saqlanib qolardi. Endi bunday holatda butun buyurtma
        orqaga qaytariladi (rollback) va aniq xato qaytariladi.
        """
        items_data = validated_data.pop("uploaded_items", [])
        order = Order.objects.create(**validated_data)

        total = 0
        try:
            for item_data in items_data:
                dish_id = item_data.get("dish")
                quantity = item_data.get("quantity", 1)

                try:
                    dish = Dish.objects.get(
                        id=dish_id, category__restaurant=order.restaurant
                    )
                except Dish.DoesNotExist:
                    raise ValidationError(
                        {"uploaded_items": f"ID={dish_id} bo'lgan taom topilmadi."}
                    )

                item = OrderItem.objects.create(
                    order=order, dish=dish, quantity=quantity, price=dish.price
                )
                total += item.price * item.quantity
        except ValidationError:
            order.delete()
            raise

        order.total_price = total
        order.save()
        return order
