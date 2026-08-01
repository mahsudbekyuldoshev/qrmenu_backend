from rest_framework.permissions import BasePermission


class IsRestaurantStaff(BasePermission):
    """
    Foydalanuvchi biror restoranga biriktirilgan xodim bo'lsa ruxsat beradi
    (director, manager, waiter yoki chef — rolidan qat'i nazar). Super Admin
    bu yerga kirmaydi, chunki u hech qanday restoranga bog'lanmagan
    (restaurant=None).
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.restaurant_id is not None)


class IsRestaurantManager(BasePermission):
    """
    TUZATISH: `director` roli qaytarilgani sabab endi bu klass ikkalasiga ham
    (director VA manager) yozish huquqi beradi — director manager qila oladigan
    hamma narsani (menyu tahrirlash, stol qo'shish, fon rasm o'zgartirish va
    h.k.) + undan ortig'ini qila oladi. Nomi tarixiy sabablarga ko'ra
    "Manager" saqlab qolindi, chunki view'larda shu nom bilan keng qo'llaniladi.

    Faqat director'ga xos (manager'ga berilmaydigan) amallar uchun pastdagi
    `IsRestaurantDirector`dan foydalaning.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role in ("director", "manager")
        )


class IsRestaurantDirector(BasePermission):
    """
    Faqat role="director" bo'lgan va restoranga biriktirilgan foydalanuvchiga
    ruxsat beradi — xodim (manager/waiter/chef) qo'shish-o'chirish, obuna
    holatini ko'rish kabi manager'ga berilmaydigan amallar uchun.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.restaurant_id is not None
            and user.role == "director"
        )


class IsSuperAdmin(BasePermission):
    """
    Faqat role="super_admin" bo'lgan foydalanuvchiga ruxsat beradi.
    Super Admin panel (restoranlar ro'yxati, obunalar, director biriktirish)
    shu permission bilan himoyalanadi.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "super_admin")
