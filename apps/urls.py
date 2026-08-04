from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.views import (
    AdminAnalyticsView,
    AdminDashboardView,
    BackgroundSearchView,
    BackgroundSelectView,
    CallWaiterView,
    CategoryViewSet,
    ChangePasswordView,
    DirectorViewSet,
    DishViewSet,
    KitchenQueueView,
    LoginView,
    MeView,
    MyRestaurantView,
    OrderItemStatusUpdateView,
    OrderViewSet,
    PublicMenuView,
    PublicOrderCreateView,
    RequestPaymentView,
    RestaurantAdminViewSet,
    StaffViewSet,
    TableViewSet,
    WaiterCallResolveView,
    WaiterQueueView,
)

router = DefaultRouter()
router.register("tables", TableViewSet, basename="table")
router.register("categories", CategoryViewSet, basename="category")
router.register("dishes", DishViewSet, basename="dish")
router.register("orders", OrderViewSet, basename="order")
router.register("staff", StaffViewSet, basename="staff")

# --- Super Admin panel ---
router.register("admin/directors", DirectorViewSet, basename="admin-directors")
router.register(
    "admin/restaurants", RestaurantAdminViewSet, basename="admin-restaurants"
)

urlpatterns = [
    # --- Auth ---
    # DIQQAT: ochiq /auth/register/ OLIB TASHLANDI. Endi barcha hisoblar
    # ierarxik ravishda yaratiladi: super_admin->director (admin/directors/),
    # director/manager->manager/waiter/chef (staff/).
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path(
        "auth/change-password/",
        ChangePasswordView.as_view(),
        name="auth-change-password",
    ),
    # --- Restoran (o'zim haqida) ---
    path("restaurant/me/", MyRestaurantView.as_view(), name="restaurant-me"),
    # --- Manager: fon rasmini qidirish/tanlash (Unsplash) ---
    path(
        "manager/backgrounds/search/",
        BackgroundSearchView.as_view(),
        name="background-search",
    ),
    path(
        "manager/backgrounds/select/",
        BackgroundSelectView.as_view(),
        name="background-select",
    ),
    # --- KDS (Oshpaz) va Waiter Station navbatlari ---
    path("kitchen/queue/", KitchenQueueView.as_view(), name="kitchen-queue"),
    path("waiter/queue/", WaiterQueueView.as_view(), name="waiter-queue"),
    path(
        "order-items/<int:pk>/status/",
        OrderItemStatusUpdateView.as_view(),
        name="order-item-status",
    ),
    path(
        "waiter-calls/<int:pk>/resolve/",
        WaiterCallResolveView.as_view(),
        name="waiter-call-resolve",
    ),
    # --- Mijoz uchun ochiq QR-menyu (auth talab qilinmaydi) ---
    path("menu/<str:qr_hash>/", PublicMenuView.as_view(), name="public-menu"),
    path(
        "menu/<str:qr_hash>/order/",
        PublicOrderCreateView.as_view(),
        name="public-order-create",
    ),
    path(
        "menu/<str:qr_hash>/call-waiter/",
        CallWaiterView.as_view(),
        name="public-call-waiter",
    ),
    path(
        "menu/<str:qr_hash>/request-payment/",
        RequestPaymentView.as_view(),
        name="public-request-payment",
    ),
    # --- Super Admin: statistika/analitika ---
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
] + router.urls
