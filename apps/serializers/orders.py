from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, JSONField, ReadOnlyField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models.orders import Order, OrderItem
from apps.models.restaurants import Dish


class OrderItemSerializer(ModelSerializer):
    """Buyurtma tarkibidagi taomlar serializeri."""

    dish_name = ReadOnlyField(source="dish.name")
    requires_kitchen = ReadOnlyField(source="dish.requires_kitchen")
    status_display = CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "order",
            "dish",
            "dish_name",
            "requires_kitchen",
            "quantity",
            "price",
            "status",
            "status_display",
        )
        read_only_fields = "id", "price", "status"


class OrderSerializer(ModelSerializer):
    """
    Buyurtma serializeri (xodimlar/staff uchun - OrderViewSet orqali
    ishlatiladi). Mijozning QR orqali ochiq buyurtma berishi uchun bu
    serializer ISHLATILMAYDI - apps/views/menu.py:PublicOrderCreateView'da
    alohida ishlanadi.
    """

    # XATOLIK EDI: `required=True` bo'lgani uchun OrderViewSet (ModelViewSet)
    # orqali PUT/PATCH qilinganda (masalan faqat `comment`ni yangilash uchun)
    # klient har safar to'liq `uploaded_items` massivini qayta yuborishga
    # majbur bo'lardi. Battari - `update()` umuman override QILINMAGANI
    # uchun PUT/PATCH'da yuborilgan `uploaded_items` hech qanday amalga
    # oshmasdi (na yangi item yaratilardi, na eski item o'zgartirilardi) -
    # instance'ga shunchaki ishlatilmaydigan atribut sifatida yozilib,
    # klientni chalg'itardi ("yubordim-ku, nega o'zgarmadi"). Endi faqat
    # create paytida majburiy, update paytida e'tiborga olinmaydi.
    items = OrderItemSerializer(many=True, read_only=True)
    uploaded_items = JSONField(write_only=True, required=False)

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
        read_only_fields = "id", "restaurant", "status", "total_price", "created_at"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Faqat YARATISHDA items majburiy - yangilashda (`self.instance`
        # mavjud bo'lsa) items o'zgartirilmaydi, shuning uchun talab
        # qilinmaydi.
        if self.instance is None and not attrs.get("uploaded_items"):
            raise ValidationError({"uploaded_items": "Kamida bitta taom kiritilishi shart."})
        return attrs

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
        request = self.context.get("request")
        if request and value and value.restaurant_id != request.user.restaurant_id:
            raise ValidationError("Bu stol sizning restoraningizga tegishli emas.")
        return value

    def create(self, validated_data):
        """
        Nested itemlar bilan buyurtmani yaratish. Noto'g'ri dish ID kelsa
        butun buyurtma orqaga qaytariladi (rollback).

        Har bir OrderItem yaratilganda `dish.requires_kitchen`ga qarab
        boshlang'ich `status` avtomatik belgilanadi (qarang: OrderItem.save()) -
        kerak bo'lmaydigan taomlar (non/suv) darhol "ready" bilan boshlanadi.
        """
        items_data = validated_data.pop("uploaded_items", [])
        order = Order.objects.create(**validated_data)

        total = 0
        try:
            for item_data in items_data:
                dish_id = item_data.get("dish")
                quantity = item_data.get("quantity", 1)

                try:
                    dish = Dish.objects.get(id=dish_id, category__restaurant=order.restaurant)
                except Dish.DoesNotExist:
                    raise ValidationError({"uploaded_items": f"ID={dish_id} bo'lgan taom topilmadi."})

                item = OrderItem.objects.create(order=order, dish=dish, quantity=quantity, price=dish.price)
                total += item.price * item.quantity
        except ValidationError:
            order.delete()
            raise

        order.total_price = total
        order.save(update_fields=["total_price"])
        order.refresh_status()
        return order

    def update(self, instance, validated_data):
        # `uploaded_items` update() orqali hech qachon qayta ishlanmaydi -
        # buyurtma tarkibini o'zgartirish uchun alohida oqim (masalan yangi
        # item qo'shish endpointi) kerak bo'ladi, bu yerda faqat
        # `table`/`comment` kabi oddiy maydonlar yangilanadi.
        validated_data.pop("uploaded_items", None)
        return super().update(instance, validated_data)


class OrderItemStatusUpdateSerializer(Serializer):
    """
    PATCH /order-items/{id}/status/
    Rolga qarab ruxsat etilgan o'tishlar view qatlamida tekshiriladi
    (qarang: OrderItemStatusUpdateView) - bu serializer faqat qiymatni
    validatsiya qiladi.
    """

    status = ChoiceField(choices=OrderItem.Status.choices)