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


class Restaurant(Model):
    """
    Restoran modeli.
    Tizimda har bir restoranning o'zining alohida sozlamalari, menyusi va stollari bo'ladi (SaaS modeli).
    """

    name = CharField(max_length=255, verbose_name="Restoran nomi")
    slug = SlugField(max_length=255, unique=True, verbose_name="Slug (URL uchun)")
    is_active = BooleanField(default=True, verbose_name="Aktivlik statusi")
    subscription_end_date = DateTimeField(
        verbose_name="Obuna tugash vaqti", null=True, blank=True
    )
    owner = ForeignKey(
        settings.AUTH_USER_MODEL,  # TUZATISH: "auth.User" o'rniga - endi custom User (apps.User)
        SET_NULL,
        null=True,
        blank=True,
        related_name="owned_restaurants",
        verbose_name="Egasi",
    )

    created_at = DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Restoran"
        verbose_name_plural = "Restoranlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Table(Model):
    """
    Stol modeli.
    Restorandagi stollar raqami yoki nomi va QR-kod uchun maxsus xavfsiz hashni saqlaydi.
    """

    restaurant = ForeignKey(
        Restaurant, CASCADE, related_name="tables", verbose_name="Restoran"
    )
    number = CharField(max_length=50, verbose_name="Stol raqami/nomi")
    qr_hash = CharField("QR kod uchun hash", max_length=64, unique=True, blank=True)
    is_active = BooleanField(default=True, verbose_name="Aktivlik statusi")

    created_at = DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = DateTimeField("Tahrirlangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Stol"
        verbose_name_plural = "Stollar"
        unique_together = ("restaurant", "number")
        ordering = ["number"]

    def save(self, *args, **kwargs):
        if not self.qr_hash:
            self.qr_hash = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.restaurant.name} - Stol №{self.number}"


class Category(Model):
    """
    Kategoriya modeli.
    """

    restaurant = ForeignKey(
        Restaurant, CASCADE, related_name="categories", verbose_name="Restoran"
    )
    name = CharField(max_length=255, verbose_name="Kategoriya nomi")
    slug = SlugField(max_length=255, verbose_name="Slug (URL uchun)")
    description = TextField(blank=True, null=True, verbose_name="Kategoriya tavsifi")
    is_active = BooleanField(default=True, verbose_name="Faollik statusi")
    ordering = IntegerField(default=0, verbose_name="Tartib raqami (Saralash uchun)")

    created_at = DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        unique_together = ("restaurant", "slug")
        ordering = ["ordering", "name"]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class Dish(Model):
    """
    Taom modeli. `is_available` — stop-list vazifasini bajaradi.
    """

    category = ForeignKey(
        Category, CASCADE, related_name="dishes", verbose_name="Kategoriya"
    )
    name = CharField("Taom nomi", max_length=255)
    description = TextField("Taom tavsifi", blank=True, null=True)
    price = DecimalField("Narxi", max_digits=10, decimal_places=2)
    image = ImageField("Taom rasmi", upload_to="dishes/", blank=True, null=True)
    is_available = BooleanField("Mavjud (Stop-list)", default=True)

    created_at = DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = DateTimeField("Tahrirlangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Taom"
        verbose_name_plural = "Taomlar"
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.restaurant.name} - {self.name} ({self.price} so'm)"
