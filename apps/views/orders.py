from rest_framework import viewsets

from apps.models.orders import Order
from apps.serializers.orders import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    Buyurtmalarni boshqarish uchun ViewSet.
    KDS (Kitchen Display System) uchun statuslar bo'yicha filterlash imkoniyati bilan.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related("restaurant", "table").prefetch_related("items", "items__dish")
        restaurant_id = self.request.query_params.get('restaurant')
        restaurant_slug = self.request.query_params.get('restaurant_slug')
        status = self.request.query_params.get('status')

        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        if restaurant_slug:
            queryset = queryset.filter(restaurant__slug=restaurant_slug)
        if status:
            statuses = [s.strip() for s in status.split(",") if s.strip()]
            queryset = queryset.filter(status__in=statuses)

        return queryset
