from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from apps.models.restaurants import Category, Dish, Restaurant


class PublicRestaurantSerializer(ModelSerializer):
    """
    Mijoz uchun ochiq (auth talab qilmaydigan) restoran ma'lumoti.
    Frontend `/menu/:id` sahifasida shu orqali `menu_background` rasmini oladi —
    bu maydonni faqat Manager (RestaurantSerializer orqali) o'zgartira oladi,
    mijoz esa bu yerda faqat o'qish (read-only) huquqiga ega.
    """

    class Meta:
        model = Restaurant
        fields = "id", "name", "slug", "menu_background"


class PublicDishSerializer(ModelSerializer):
    """Mijoz uchun ochiq (auth talab qilmaydigan) taom ma'lumoti."""

    class Meta:
        model = Dish
        fields = "id", "name", "description", "price", "image"


class PublicCategorySerializer(ModelSerializer):
    """Mijoz uchun ochiq kategoriya — faqat mavjud (is_available=True) taomlar bilan."""

    dishes = SerializerMethodField()

    class Meta:
        model = Category
        fields = "id", "name", "dishes"

    def get_dishes(self, obj):
        available = obj.dishes.filter(is_available=True)
        return PublicDishSerializer(available, many=True).data