from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orders.views.views import OrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
