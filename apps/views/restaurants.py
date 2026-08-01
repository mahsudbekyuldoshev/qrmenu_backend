from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from apps.models.restaurants import Category, Dish, Table
from apps.permission import IsRestaurantManager, IsRestaurantStaff
from apps.serializers.restaurants import (
    CategorySerializer,
    DishSerializer,
    RestaurantSerializer,
    TableSerializer,
)


class MyRestaurantView(RetrieveUpdateAPIView):
    """
    GET: har qanday xodim (director/manager/ofitsiant/oshpaz) o'z restorani
    ma'lumotini ko'radi.
    PATCH/PUT: director YOKI manager tahrirlashi mumkin (`IsRestaurantManager`
    endi ikkalasini ham qamrab oladi) - masalan menu_background, restoran nomi
    va h.k. shu orqali o'zgartiriladi.
    """

    serializer_class = RestaurantSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), IsRestaurantManager()]
        return [IsAuthenticated()]

    def get_object(self):
        restaurant = self.request.user.restaurant
        if restaurant is None:
            raise PermissionDenied("Sizga tegishli restoran topilmadi.")
        return restaurant


class TableViewSet(viewsets.ModelViewSet):
    """Director yoki manager stollarni boshqaradi (yaratadi/o'chiradi)."""

    serializer_class = TableSerializer
    permission_classes = (IsAuthenticated, IsRestaurantManager)

    def get_queryset(self):
        return Table.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Menyu kategoriyalari.

    - GET (list/retrieve): istalgan restoran xodimi (director/manager/waiter/chef)
      ko'ra oladi - chunki oshpaz KDS panelida, ofitsiant esa buyurtma
      ekranida menyuni ko'rishi kerak.
    - POST/PUT/PATCH/DELETE: faqat director yoki manager.
    """

    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated(), IsRestaurantManager()]
        return [IsAuthenticated(), IsRestaurantStaff()]

    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class DishViewSet(viewsets.ModelViewSet):
    """
    Taomlar (narx, stop-list va h.k.).

    Oshpaz (chef) taomlarni FAQAT ko'radi (KDS panelida "Menyu" bo'limi
    read-only bo'lishi shart), lekin qo'sha/tahrirlay/o'chira olmaydi.
    Bu huquq director va manager uchun.
    """

    serializer_class = DishSerializer
    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated(), IsRestaurantManager()]
        return [IsAuthenticated(), IsRestaurantStaff()]

    def get_queryset(self):
        return Dish.objects.filter(category__restaurant=self.request.user.restaurant)