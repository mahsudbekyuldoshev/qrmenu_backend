import uuid

from django.conf import settings
from django.db.models import (
    CASCADE,
    SET_NULL,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    ImageField,
    IntegerField,
    Model,
    SlugField,
    TextField,
)
from django.utils.translation import gettext_lazy as _


class Restaurant(Model):
    """
    Restoran modeli. Har bir restoranning o'zining alohida sozlamalari,
    menyusi va stollari bo'ladi (SaaS modeli). Restoranning platformadan
    foydalanish huquqi `subscription_info` (Subscription) orqali aniqlanadi.
    """

    name = CharField(_("Restoran nomi"), max_length=255)
    slug = SlugField(_("Slug (URL uchun)"), max_length=255, unique=True)
    is_active = BooleanField(_("Aktivlik statusi"), default=True)
    menu_background = ImageField(
        _("Menyu fon rasmi"),
        upload_to="restaurant_backgrounds/",
        blank=True,
        null=True,
        help_text=_("Mijoz QR-menyu sahifasining fon rasmi (Manager panel orqali o'zgartiriladi)."),
    )
    owner = ForeignKey(
        settings.AUTH_USER_MODEL,
        SET_NULL,
        null=True,
        blank=True,
        related_name="owned_restaurants",
        verbose_name=_("Direktori"),
        help_text=_("Restoranga biriktirilgan direktor (role=director), Super Admin panel orqali tayinlanadi."),
    )

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Restoran")
        verbose_name_plural = _("Restoranlar")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Table(Model):
    """Stol modeli. QR-kod uchun maxsus xavfsiz hashni saqlaydi."""

    restaurant = ForeignKey(Restaurant, CASCADE, related_name="tables", verbose_name=_("Restoran"))
    number = CharField(_("Stol raqami/nomi"), max_length=50)
    qr_hash = CharField(_("QR kod uchun hash"), max_length=64, unique=True, blank=True)
    is_active = BooleanField(_("Aktivlik statusi"), default=True)

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Stol")
        verbose_name_plural = _("Stollar")
        unique_together = ("restaurant", "number")
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if not self.qr_hash:
            self.qr_hash = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.restaurant.name} - Stol №{self.number}"


class Category(Model):
    """Kategoriya modeli."""

    restaurant = ForeignKey(
        "apps.Restaurant", CASCADE, related_name="categories", verbose_name=_("Restoran")
    )
    name = CharField(_("Kategoriya nomi"), max_length=255)
    slug = SlugField(_("Slug (URL uchun)"), max_length=255)
    description = TextField(_("Kategoriya tavsifi"), blank=True, null=True)
    is_active = BooleanField(_("Faollik statusi"), default=True)
    ordering = IntegerField(_("Tartib raqami (Saralash uchun)"), default=0)

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        unique_together = ("restaurant", "slug")
        ordering = ["ordering", "name"]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class Dish(Model):
    """
    Taom modeli. `is_available` - stop-list vazifasini bajaradi.

    `requires_kitchen` - BUYURTMA OQIMI uchun eng muhim maydon:
        True  (default) - taom oshxonada tayyorlanishi kerak (masalan osh,
               shashlik). Buyurtma qilinganda avval CHEF navbatiga tushadi,
               chef "Tayyor" tugmasini bosgach - Waiter navbatiga o'tadi.
        False - tayyor mahsulot (non, suv, ichimlik va h.k.). Oshxonaga
               umuman TUSHMAYDI - buyurtma qilinishi bilan to'g'ridan-to'g'ri
               Waiter navbatiga "yetkazishga tayyor" holatida tushadi.
    """

    category = ForeignKey(Category, CASCADE, related_name="dishes", verbose_name=_("Kategoriya"))
    name = CharField(_("Taom nomi"), max_length=255)
    description = TextField(_("Taom tavsifi"), blank=True, null=True)
    price = DecimalField(_("Narxi"), max_digits=10, decimal_places=2)
    image = ImageField(_("Taom rasmi"), upload_to="dishes/", blank=True, null=True)
    is_available = BooleanField(_("Mavjud (Stop-list)"), default=True)
    requires_kitchen = BooleanField(
        _("Oshxonada tayyorlanadi"),
        default=True,
        help_text=_(
            "Yoqilgan bo'lsa - buyurtma avval Oshpaz (KDS) navbatiga tushadi. "
            "O'chirilgan bo'lsa (non, suv, ichimlik kabi tayyor mahsulotlar) - "
            "oshxonani chetlab, to'g'ridan-to'g'ri Ofitsiant navbatiga tushadi."
        ),
    )

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Taom")
        verbose_name_plural = _("Taomlar")
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.restaurant.name} - {self.name} ({self.price} so'm)"