from rest_framework.permissions import BasePermission


class IsRestaurantStaff(BasePermission):
    """
    Foydalanuvchi biror restoranga biriktirilgan xodim bo'lsa ruxsat beradi
    (manager, waiter yoki chef — rolidan qat'i nazar). Super Admin bu yerga
    kirmaydi, chunki u hech qanday restoranga bog'lanmagan (restaurant=None).
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
        )


class IsRestaurantManager(BasePermission):
    """
    TUZATISH: avvalgi `IsRestaurantOwner`ning o'rnini bosadi — role nomi
    "owner" dan "manager"ga o'zgargani uchun.

    Faqat role="manager" bo'lgan va restoranga biriktirilgan foydalanuvchiga
    yozish (menyu tahrirlash, stol qo'shish, fon rasm o'zgartirish va h.k.)
    huquqini beradi.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == "manager"
        )


class IsSuperAdmin(BasePermission):
    """
    Faqat role="super_admin" bo'lgan foydalanuvchiga ruxsat beradi.
    Super Admin panel (restoranlar ro'yxati, obunalar, manager biriktirish)
    shu permission bilan himoyalanadi.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role == "super_admin"
        )