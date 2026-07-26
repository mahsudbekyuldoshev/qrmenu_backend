from rest_framework import viewsets
from ..models.models import Restaurant, Table, Category, Dish
from ..serializers.serializers import RestaurantSerializer, TableSerializer, CategorySerializer, DishSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    """
    Restoranlarni boshqarish uchun ViewSet.
    """
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    lookup_field = 'slug'


class TableViewSet(viewsets.ModelViewSet):
    """
    Stollarni boshqarish uchun ViewSet.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    
    def get_queryset(self):
        # Agar URL'da restaurant_id bo'lsa, faqat o'sha restoranga tegishli stollarni qaytaradi
        queryset = Table.objects.all()
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Kategoriyalarni boshqarish uchun ViewSet.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.prefetch_related("dishes")
        restaurant_id = self.request.query_params.get('restaurant')
        restaurant_slug = self.request.query_params.get('restaurant_slug')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        if restaurant_slug:
            queryset = queryset.filter(restaurant__slug=restaurant_slug)
        return queryset


class DishViewSet(viewsets.ModelViewSet):
    """
    Taomlarni boshqarish uchun ViewSet.
    """
    queryset = Dish.objects.all()
    serializer_class = DishSerializer

    def get_queryset(self):
        queryset = Dish.objects.select_related("category", "category__restaurant")
        category_id = self.request.query_params.get('category')
        restaurant_id = self.request.query_params.get('restaurant')
        restaurant_slug = self.request.query_params.get('restaurant_slug')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if restaurant_id:
            queryset = queryset.filter(category__restaurant_id=restaurant_id)
        if restaurant_slug:
            queryset = queryset.filter(category__restaurant__slug=restaurant_slug)
        return queryset
