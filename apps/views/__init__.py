from apps.views.auth import ChangePasswordView, LoginView, MeView
from apps.views.background import BackgroundSearchView, BackgroundSelectView
from apps.views.menu import (
    CallWaiterView,
    PublicMenuView,
    PublicOrderCreateView,
    RequestPaymentView,
    WaiterCallResolveView,
)
from apps.views.orders import (
    KitchenQueueView,
    OrderItemStatusUpdateView,
    OrderViewSet,
    WaiterQueueView,
)
from apps.views.restaurants import (
    CategoryViewSet,
    DishViewSet,
    MyRestaurantView,
    TableViewSet,
)
from apps.views.staff import StaffViewSet
from apps.views.super_admin import (
    AdminAnalyticsView,
    AdminDashboardView,
    DirectorViewSet,
    RestaurantAdminViewSet,
)