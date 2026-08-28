from rest_framework.permissions import BasePermission

from apps.models.users import User


class IsRestaurantStaff(BasePermission):
    """
    Restoranga biriktirilgan xodim bo'lsa ruxsat beradi (director, manager,
    waiter yoki chef - rolidan qat'i nazar). Ishdan ketgan/haydalgan xodim
    (`employment_status != WORKING`) ham bloklanadi - login vaqtida
    is_active=False qilingani uchun avtomatik JWT auth orqali chetlanadi.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
        )


class IsRestaurantManagerOnly(BasePermission):
    """
    QAT'IY faqat role="manager". Menyu (kategoriya/taom) tahrirlash, fon
    rasm o'zgartirish, stollarni boshqarish shu klass bilan cheklanadi.

    MUHIM: director bu yerga KIRMAYDI - director menyuni faqat GET orqali
    (IsRestaurantStaff) ko'radi, lekin yoza olmaydi. Bu ataylab shunday -
    "restoran egasi kuzatib boradi, operatsion boshqaruvni manager qiladi"
    tamoyili.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == User.Role.MANAGER
        )


class IsRestaurantDirectorOnly(BasePermission):
    """QAT'IY faqat role="director"."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == User.Role.DIRECTOR
        )


class IsRestaurantDirectorOrManager(BasePermission):
    """
    director VA manager uchun - xodimlarni (waiter/chef, director uchun
    manager ham) boshqarish kabi ikkalasiga ham tegishli amallar uchun.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role in (User.Role.DIRECTOR, User.Role.MANAGER)
        )


class IsRestaurantChef(BasePermission):
    """Faqat oshpaz (chef) - KDS navbatini boshqarish uchun."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == User.Role.CHEF
        )


class IsRestaurantWaiter(BasePermission):
    """Faqat ofitsiant (waiter) - Waiter Station navbatini boshqarish uchun."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == User.Role.WAITER
        )


class IsSuperAdmin(BasePermission):
    """Faqat role="super_admin". Super Admin panel shu bilan himoyalanadi."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role == User.Role.SUPER_ADMIN
        )