from rest_framework import serializers

from apps.models.restaurants import Category, Dish, Restaurant, Table


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "subscription_end_date",
            "owner",
            "created_at",
        )

        read_only_fields = (
            "id",
            "slug",
            "is_active",
            "subscription_end_date",
            "owner",
            "created_at",
        )


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = "id", "restaurant", "number", "qr_hash", "is_active"
        read_only_fields = "id", "restaurant", "qr_hash"


class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = (
            "id",
            "category",
            "name",
            "description",
            "price",
            "image",
            "is_available",
        )

    def validate_category(self, value):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if value.restaurant.owner_id != request.user.id:
                raise serializers.ValidationError(
                    "Bu kategoriya sizning restoraningizga tegishli emas."
                )
        return value


class CategorySerializer(serializers.ModelSerializer):
    dishes = DishSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "restaurant",
            "name",
            "slug",
            "description",
            "is_active",
            "ordering",
            "dishes",
        )
        read_only_fields = "id", "restaurant"
