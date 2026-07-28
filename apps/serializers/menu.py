from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from apps.models.restaurants import Category, Dish


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
