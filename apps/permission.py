from rest_framework import permissions


class IsRestaurantStaff(permissions.BasePermission):
    """
    Foydalanuvchi biror restoranga xodim sifatida biriktirilganini tekshiradi
    (direktor, ofitsiant yoki oshpaz — barchasi uchun ishlaydi).
    Masalan OrderViewSet uchun mos: buyurtma statusini har uchala rol ham o'zgartiradi.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.restaurant_id
        )

    def has_object_permission(self, request, view, obj):
        restaurant = getattr(obj, "restaurant", obj)
        return request.user.restaurant_id == restaurant.id


class IsRestaurantOwner(IsRestaurantStaff):
    """
    Faqat restoran DIREKTORI uchun — menyu, stol, restoran sozlamalarini
    boshqarish kabi amallar uchun (ofitsiant/oshpaz bularga kira olmasligi kerak).
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == request.user.Role.OWNER