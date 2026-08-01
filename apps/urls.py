from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.views import (
    AdminDashboardView,
    CategoryViewSet,
    DirectorViewSet,
    DishViewSet,
    LoginView,
    MeView,
    MyRestaurantView,
    OrderViewSet,
    PublicMenuView,
    PublicOrderCreateView,
    RegisterView,
    RestaurantAdminViewSet,
    TableViewSet,
)

router = DefaultRouter()
router.register("tables", TableViewSet, basename="table")
router.register("categories", CategoryViewSet, basename="category")
router.register("dishes", DishViewSet, basename="dish")
router.register("orders", OrderViewSet, basename="order")

# --- Super Admin panel (direktor/restoran/obuna boshqaruvi) ---
router.register("admin/directors", DirectorViewSet, basename="admin-directors")
router.register(
    "admin/restaurants", RestaurantAdminViewSet, basename="admin-restaurants"
)

urlpatterns = [
    # --- Auth ---
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    # --- Direktor/xodim uchun (APIView, faqat "mening restoranim") ---
    path("restaurant/me/", MyRestaurantView.as_view(), name="restaurant-me"),
    # --- Mijoz uchun ochiq QR-menyu (APIView, auth talab qilinmaydi) ---
    path("menu/<str:qr_hash>/", PublicMenuView.as_view(), name="public-menu"),
    path(
        "menu/<str:qr_hash>/order/",
        PublicOrderCreateView.as_view(),
        name="public-order-create",
    ),
    # --- Super Admin bosh sahifasi (statistika) ---
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
] + router.urls
