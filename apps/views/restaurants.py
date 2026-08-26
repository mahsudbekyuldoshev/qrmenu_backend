from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from apps.models.restaurants import Category, Dish, Table
from apps.permission import IsRestaurantManagerOnly, IsRestaurantStaff
from apps.serializers.restaurants import (
    CategorySerializer,
    DishSerializer,
    RestaurantSerializer,
    TableSerializer,
)


@extend_schema(tags=["Restaurant"])
class MyRestaurantView(RetrieveUpdateAPIView):
    """
    GET: har qanday xodim (director/manager/waiter/chef) o'z restorani
    ma'lumotini ko'radi.
    PATCH/PUT: FAQAT manager (menu_background, restoran nomi va h.k.).

    TUZATISH: director endi bu yerga YOZA OLMAYDI - director restoranni
    faqat kuzatib boradi (GET), operatsion tahrirlash huquqi faqat
    manager'da.
    """

    serializer_class = RestaurantSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), IsRestaurantManagerOnly()]
        return [IsAuthenticated()]

    def get_object(self):
        restaurant = self.request.user.restaurant
        if restaurant is None:
            raise PermissionDenied("Sizga tegishli restoran topilmadi.")
        return restaurant


@extend_schema_view(
    list=extend_schema(tags=["Manager / Tables"]),
    retrieve=extend_schema(tags=["Manager / Tables"]),
    create=extend_schema(tags=["Manager / Tables"]),
    update=extend_schema(tags=["Manager / Tables"]),
    partial_update=extend_schema(tags=["Manager / Tables"]),
    destroy=extend_schema(tags=["Manager / Tables"]),
)
class TableViewSet(viewsets.ModelViewSet):
    """Faqat manager stollarni boshqaradi (yaratadi/o'chiradi)."""

    serializer_class = TableSerializer
    permission_classes = (IsAuthenticated, IsRestaurantManagerOnly)

    def get_queryset(self):
        return Table.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


@extend_schema_view(
    list=extend_schema(tags=["Menu / Categories"]),
    retrieve=extend_schema(tags=["Menu / Categories"]),
    create=extend_schema(tags=["Menu / Categories"]),
    update=extend_schema(tags=["Menu / Categories"]),
    partial_update=extend_schema(tags=["Menu / Categories"]),
    destroy=extend_schema(tags=["Menu / Categories"]),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Menyu kategoriyalari.
    - GET (list/retrieve): istalgan restoran xodimi (director/manager/
      waiter/chef) ko'ra oladi.
    - POST/PUT/PATCH/DELETE: FAQAT manager (director EMAS).
    """

    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated(), IsRestaurantManagerOnly()]
        return [IsAuthenticated(), IsRestaurantStaff()]

    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


@extend_schema_view(
    list=extend_schema(tags=["Menu / Dishes"]),
    retrieve=extend_schema(tags=["Menu / Dishes"]),
    create=extend_schema(tags=["Menu / Dishes"]),
    update=extend_schema(tags=["Menu / Dishes"]),
    partial_update=extend_schema(tags=["Menu / Dishes"]),
    destroy=extend_schema(tags=["Menu / Dishes"]),
)
class DishViewSet(viewsets.ModelViewSet):
    """
    Taomlar. Oshpaz (chef) va director FAQAT ko'radi (read-only), yozish
    huquqi FAQAT manager'da.
    """

    serializer_class = DishSerializer
    permission_classes = (IsAuthenticated, IsRestaurantStaff)

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            return [IsAuthenticated(), IsRestaurantManagerOnly()]
        return [IsAuthenticated(), IsRestaurantStaff()]

    def get_queryset(self):
        return Dish.objects.filter(category__restaurant=self.request.user.restaurant)