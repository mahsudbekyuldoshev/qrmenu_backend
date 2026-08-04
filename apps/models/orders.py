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
    Buyurtma modeli. Mijoz tomonidan stol orqali berilgan buyurtmalarni
    boshqaradi. `status` - butun buyurtmaning umumiy holati (barcha
    itemlar yetkazilganda avtomatik 'closed'ga o'tadi, qarang: OrderItem).
    """

    class Status(TextChoices):
        PENDING = "pending", _("Kutilmoqda")
        PREPARING = "preparing", _("Tayyorlanmoqda")
        READY = "ready", _("Tayyor")
        DELIVERED = "delivered", _("Yetkazildi")
        CLOSED = "closed", _("Yopilgan")

    restaurant = ForeignKey("apps.Restaurant", CASCADE, related_name="orders", verbose_name=_("Restoran"))
    table = ForeignKey(
        "apps.Table", SET_NULL, null=True, blank=True, related_name="orders", verbose_name=_("Stol")
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

    def refresh_status(self):
        """
        Barcha item'lar holatidan kelib chiqib Order.status'ni yangilaydi.
        Har safar OrderItem.status o'zgarganda chaqiriladi (signal yoki
        view'dan qo'lda).
        """
        statuses = list(self.items.values_list("status", flat=True))
        if not statuses:
            return
        if all(s == OrderItem.Status.DELIVERED for s in statuses):
            self.status = self.Status.CLOSED
        elif any(s == OrderItem.Status.READY for s in statuses):
            self.status = self.Status.READY
        elif any(s == OrderItem.Status.PREPARING for s in statuses):
            self.status = self.Status.PREPARING
        else:
            self.status = self.Status.PENDING
        self.save(update_fields=["status"])


class OrderItem(Model):
    """
    Buyurtma tarkibidagi taomlar.

    `status` - BUYURTMA OQIMINING yuragi:
        PENDING    - yaratilgan, hali ishlanmagan
                     (dish.requires_kitchen=True bo'lsa shu holatda boshlanadi
                     va Oshpaz/KDS navbatida ko'rinadi)
        PREPARING  - oshpaz tayyorlashni boshladi (ixtiyoriy oraliq holat)
        READY      - tayyor, Ofitsiant navbatida ko'rinadi va yetkazilishi
                     kerak. dish.requires_kitchen=False bo'lgan itemlar
                     (non, suv va h.k.) YARATILISHDA DARHOL shu holatda
                     boshlanadi - oshxonani chetlab o'tadi.
        DELIVERED  - ofitsiant mijozga yetkazib berdi, jarayon tugadi
    """

    class Status(TextChoices):
        PENDING = "pending", _("Kutilmoqda")
        PREPARING = "preparing", _("Tayyorlanmoqda")
        READY = "ready", _("Tayyor / Yetkazishga tayyor")
        DELIVERED = "delivered", _("Yetkazildi")

    order = ForeignKey("apps.Order", CASCADE, related_name="items", verbose_name=_("Buyurtma"))
    dish = ForeignKey("apps.Dish", SET_NULL, null=True, verbose_name=_("Taom"))
    quantity = PositiveIntegerField(_("Soni"), default=1)
    price = DecimalField(_("Narxi (sotuv vaqtidagi)"), max_digits=10, decimal_places=2)
    status = CharField(
        _("Holati"), max_length=20, choices=Status.choices, default=Status.PENDING
    )

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = DateTimeField(_("Tahrirlangan vaqt"), auto_now=True)

    class Meta:
        verbose_name = _("Buyurtma taomi")
        verbose_name_plural = _("Buyurtma taomlari")

    def __str__(self):
        dish_name = self.dish.name if self.dish else str(_("O'chirilgan taom"))
        return f"{dish_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price and self.dish:
            self.price = self.dish.price
        # Oshxona kerak bo'lmagan taom (non, suv...) - darhol "tayyor"
        # holatda boshlanadi, KDS navbatiga umuman tushmaydi.
        is_new = self._state.adding
        if is_new and self.dish and not self.dish.requires_kitchen:
            self.status = self.Status.READY
        super().save(*args, **kwargs)