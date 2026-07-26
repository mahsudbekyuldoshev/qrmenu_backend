from rest_framework import serializers
from apps.orders.models.models import Order, OrderItem
from restaurants.models.models import Dish

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Buyurtma tarkibidagi taomlar serializeri.
    """
    dish_name = serializers.ReadOnlyField(source='dish.name')
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'dish', 'dish_name', 'quantity', 'price']
        read_only_fields = ['id', 'price'] # Narx save() metodida avtomatik olinadi


class OrderSerializer(serializers.ModelSerializer):
    """
    Buyurtma serializeri.
    Buyurtma yaratishda itemlarni ham birga yuborish imkoniyatini beradi.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    # Faqat yaratish uchun ishlatiladigan maydon
    uploaded_items = serializers.JSONField(write_only=True, required=False)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    restaurant_name = serializers.ReadOnlyField(source='restaurant.name')
    table_number = serializers.ReadOnlyField(source='table.number')

    class Meta:
        model = Order
        fields = [
            'id', 'restaurant', 'restaurant_name', 'table', 'table_number', 
            'status', 'status_display', 'total_price', 'comment', 
            'items', 'uploaded_items', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']

    def create(self, validated_data):
        """
        Nested itemlar bilan buyurtmani yaratish.
        """
        items_data = validated_data.pop('uploaded_items', [])
        order = Order.objects.create(**validated_data)
        
        total = 0
        for item_data in items_data:
            dish_id = item_data.get('dish')
            quantity = item_data.get('quantity', 1)
            
            try:
                dish = Dish.objects.get(id=dish_id)
                item = OrderItem.objects.create(
                    order=order,
                    dish=dish,
                    quantity=quantity,
                    price=dish.price
                )
                total += item.price * item.quantity
            except Dish.DoesNotExist:
                continue
        
        order.total_price = total
        order.save()
        return order
