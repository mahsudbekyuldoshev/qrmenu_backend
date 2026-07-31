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


class Order(Model):
    """
    Buyurtma modeli.
    Mijoz tomonidan stol orqali berilgan buyurtmalarni boshqaradi.
    """

    # Buyurtma holatlari (Statuslar)
    class Status(TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PREPARING = "preparing", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        DELIVERED = "delivered", "Yetkazildi"
        CLOSED = "closed", "Yopilgan"

    restaurant = ForeignKey(
        "apps.Restaurant", CASCADE, related_name="orders", verbose_name="Restoran"
    )
    table = ForeignKey(
        "apps.Table",
        SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Stol",
    )
    status = CharField(
        "Buyurtma holati", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    total_price = DecimalField(
        "Umumiy summa", max_digits=12, decimal_places=2, default=0
    )
    comment = TextField("Mijoz izohi", blank=True, null=True)

    created_at = DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = DateTimeField("Tahrirlangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.restaurant.name} ({self.get_status_display()})"


class OrderItem(Model):
    """
    Buyurtma tarkibidagi taomlar.
    Har bir taomning buyurtma qilingan vaqtdagi narxi va sonini saqlaydi.
    """

    order = ForeignKey(
        "apps.Order", CASCADE, related_name="items", verbose_name="Buyurtma"
    )
    dish = ForeignKey("apps.Dish", SET_NULL, null=True, verbose_name="Taom")
    quantity = PositiveIntegerField("Soni", default=1)
    price = DecimalField("Narxi (sotuv vaqtidagi)", max_digits=10, decimal_places=2)

    created_at = DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Buyurtma taomi"
        verbose_name_plural = "Buyurtma taomlari"

    def __str__(self):
        return (
            f"{self.dish.name if self.dish else "O'chirilgan taom"} x {self.quantity}"
        )

    def save(self, *args, **kwargs):
        if not self.price and self.dish:
            self.price = self.dish.price
        super().save(*args, **kwargs)
