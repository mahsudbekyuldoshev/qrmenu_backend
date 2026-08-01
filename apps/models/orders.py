from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    PositiveIntegerField,
    TextField,
)
from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _


class Order(Model):
    """
    Buyurtma modeli.
    Mijoz tomonidan stol orqali berilgan buyurtmalarni boshqaradi.
    """

    class Status(TextChoices):
        PENDING = "pending", _("Kutilmoqda")
        PREPARING = "preparing", _("Tayyorlanmoqda")
        READY = "ready", _("Tayyor")
        DELIVERED = "delivered", _("Yetkazildi")
        CLOSED = "closed", _("Yopilgan")

    restaurant = ForeignKey(
        "apps.Restaurant", CASCADE, related_name="orders", verbose_name=_("Restoran")
    )
    table = ForeignKey(
        "apps.Table",
        SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Stol"),
    )
    status = CharField(
        _("Buyurtma holati"), max_length=20, choices=Status.choices, default=Status.PENDING
    )
    total_price = DecimalField(_("Umumiy summa"), max_digits=12, decimal_places=2, default=0)
    comment = TextField(_("Mijoz izohi"), blank=True, null=True)

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.restaurant.name} ({self.get_status_display()})"


class OrderItem(Model):
    """
    Buyurtma tarkibidagi taomlar.
    Har bir taomning buyurtma qilingan vaqtdagi narxi va sonini saqlaydi.
    """

    order = ForeignKey("apps.Order", CASCADE, related_name="items", verbose_name=_("Buyurtma"))
    dish = ForeignKey("apps.Dish", SET_NULL, null=True, verbose_name=_("Taom"))
    quantity = PositiveIntegerField(_("Soni"), default=1)
    price = DecimalField(_("Narxi (sotuv vaqtidagi)"), max_digits=10, decimal_places=2)

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)

    class Meta:
        verbose_name = _("Buyurtma taomi")
        verbose_name_plural = _("Buyurtma taomlari")

    def __str__(self):
        dish_name = self.dish.name if self.dish else str(_("O'chirilgan taom"))
        return f"{dish_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price and self.dish:
            self.price = self.dish.price
        super().save(*args, **kwargs)