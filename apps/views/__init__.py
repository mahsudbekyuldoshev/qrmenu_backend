from apps.views.auth import LoginView, MeView, RegisterView
from apps.views.menu import PublicMenuView, PublicOrderCreateView
from apps.views.orders import OrderViewSet
from apps.views.restaurants import (
    CategoryViewSet,
    DishViewSet,
    MyRestaurantView,
    TableViewSet,
)
from apps.views.super_admin import (
    AdminDashboardView,
    DirectorViewSet,
    RestaurantAdminViewSet,
)
