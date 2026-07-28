from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.models.restaurants import Category, Dish, Table
from apps.permission import IsRestaurantOwner
from apps.serializers.restaurants import (
    CategorySerializer,
    DishSerializer,
    RestaurantSerializer,
    TableSerializer,
)


class MyRestaurantView(generics.RetrieveUpdateAPIView):
    """
    GET: har qanday xodim (direktor/ofitsiant/oshpaz) o'z restorani ma'lumotini ko'radi.
    PATCH/PUT: FAQAT direktor (role=OWNER) tahrirlashi mumkin — get_permissions() orqali.
    """

    serializer_class = RestaurantSerializer
    permission_classes = IsAuthenticated

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return IsAuthenticated(), IsRestaurantOwner()
        return IsAuthenticated()

    def get_object(self):
        restaurant = self.request.user.restaurant
        if restaurant is None:
            raise PermissionDenied("Sizga tegishli restoran topilmadi.")
        return restaurant


class TableViewSet(viewsets.ModelViewSet):
    """Faqat direktor stollarni boshqaradi (yaratadi/o'chiradi)."""

    serializer_class = TableSerializer
    permission_classes = IsAuthenticated, IsRestaurantOwner

    def get_queryset(self):
        return Table.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class CategoryViewSet(viewsets.ModelViewSet):
    """Faqat direktor menyu kategoriyalarini boshqaradi."""

    serializer_class = CategorySerializer
    permission_classes = IsAuthenticated, IsRestaurantOwner

    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class DishViewSet(viewsets.ModelViewSet):
    """Faqat direktor taomlarni boshqaradi (narx, stop-list va h.k.)."""

    serializer_class = DishSerializer
    permission_classes = IsAuthenticated, IsRestaurantOwner

    def get_queryset(self):
        return Dish.objects.filter(category__restaurant=self.request.user.restaurant)
