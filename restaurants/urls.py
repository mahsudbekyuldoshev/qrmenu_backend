from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.views import RestaurantViewSet, TableViewSet, CategoryViewSet, DishViewSet

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'tables', TableViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'dishes', DishViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
