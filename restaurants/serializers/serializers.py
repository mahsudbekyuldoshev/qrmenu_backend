from rest_framework import serializers
from ..models.models import Restaurant, Table, Category, Dish

class RestaurantSerializer(serializers.ModelSerializer):
    """
    Restoran ma'lumotlarini serializer qilish uchun.
    """
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'slug', 'is_active', 'subscription_end_date', 'owner', 'created_at']
        read_only_fields = ['id', 'created_at', 'owner']


class TableSerializer(serializers.ModelSerializer):
    """
    Stollar ma'lumotlari uchun.
    qr_hash faqat o'qish uchun (read_only), chunki u model darajasida generatsiya qilinadi.
    """
    class Meta:
        model = Table
        fields = ['id', 'restaurant', 'number', 'qr_hash', 'is_active']
        read_only_fields = ['id', 'qr_hash']


class DishSerializer(serializers.ModelSerializer):
    """
    Taomlar ma'lumotlari uchun.
    """
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Dish
        fields = ['id', 'category', 'category_name', 'name', 'description', 'price', 'image', 'is_available']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    """
    Kategoriyalar va ularga tegishli taomlar (ixtiyoriy ravishda nested).
    """
    # Agar kategoriya bilan birga uning taomlarini ham chiqarmoqchi bo'lsak:
    dishes = DishSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'restaurant', 'name', 'slug', 'description', 'is_active', 'ordering', 'dishes']
        read_only_fields = ['id']
