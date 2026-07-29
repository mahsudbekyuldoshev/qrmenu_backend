from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.models.orders import Order
from apps.permission import IsRestaurantStaff
from apps.serializers.orders import OrderSerializer


class OrderViewSet(ModelViewSet):
    """
    Buyurtmalar — direktor, ofitsiant VA oshpaz uchun ham ochiq (IsRestaurantStaff),
    chunki KDS (oshpaz) va Waiter (ofitsiant) ekranlari ham shu API orqali statusni
    o'zgartiradi. Faqat direktorga cheklab qo'yish noto'g'ri bo'lardi.
    """

    serializer_class = OrderSerializer
    permission_classes = IsAuthenticated, IsRestaurantStaff

    def get_queryset(self):
        queryset = (
            Order.objects.filter(restaurant=self.request.user.restaurant)
            .select_related("restaurant", "table")
            .prefetch_related("items", "items__dish")
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            queryset = queryset.filter(status__in=statuses)
        return queryset

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)
