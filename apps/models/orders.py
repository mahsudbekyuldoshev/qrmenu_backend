from apps.models.restaurants import Restaurant, Table, Dish
from django.db.models import Model, ForeignKey, CASCADE, CharField, DecimalField, TextField, DateTimeField, \
    PositiveIntegerField, SET_NULL
from django.db.models.enums import TextChoices


class Order(Model):
    """
    Buyurtma modeli.
    Mijoz tomonidan stol orqali berilgan buyurtmalarni boshqaradi.
    """

    # Buyurtma holatlari (Statuslar)
    class Status(TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        PREPARING = 'preparing', 'Tayyorlanmoqda'
        READY = 'ready', 'Tayyor'
        DELIVERED = 'delivered', 'Yetkazildi'
        CLOSED = 'closed', 'Yopilgan'

    restaurant = ForeignKey(
        Restaurant,
        CASCADE,
        related_name="orders",
        verbose_name="Restoran"
    )
    table = ForeignKey(
        Table,
        SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Stol"
    )
    status = CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Buyurtma holati"
    )
    total_price = DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Umumiy summa"
    )
    comment = TextField(blank=True, null=True, verbose_name="Mijoz izohi")

    created_at = DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

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
        Order,
        CASCADE,
        related_name="items",
        verbose_name="Buyurtma"
    )
    dish = ForeignKey(
        Dish,
        SET_NULL,
        null=True,
        verbose_name="Taom"
    )
    quantity = PositiveIntegerField(default=1, verbose_name="Soni")
    price = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Narxi (sotuv vaqtidagi)"
    )

    created_at = DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Buyurtma taomi"
        verbose_name_plural = "Buyurtma taomlari"

    def __str__(self):
        return f"{self.dish.name if self.dish else 'O\'chirilgan taom'} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Agar narx ko'rsatilmagan bo'lsa, taomning joriy narxini oladi
        if not self.price and self.dish:
            self.price = self.dish.price
        super().save(*args, **kwargs)
