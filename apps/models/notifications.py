from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
)
from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _


class WaiterCall(Model):
    """
    Mijoz QR-menyudagi "Ofitsiant" yoki "To'lov" tugmasini bosganda
    yaratiladigan chaqiruv. Waiter Station ekranida (barcha ofitsiantlar
    ko'radigan umumiy navbat) real-time ko'rinadi.

    - SERVICE: oddiy chaqiruv ("ofitsiant kerak" - masalan qo'shimcha
      buyurtma, salfetka va h.k.) - `amount` bo'sh.
    - PAYMENT: mijoz to'lov qilmoqchi - `amount` shu paytdagi umumiy
      buyurtma summasini saqlaydi, ofitsiant hisob-kitobni tayyorlab
      boradi.
    """

    class CallType(TextChoices):
        SERVICE = "service", _("Xizmat chaqiruvi")
        PAYMENT = "payment", _("To'lov so'rovi")

    class Status(TextChoices):
        PENDING = "pending", _("Kutilmoqda")
        RESOLVED = "resolved", _("Bajarildi")

    restaurant = ForeignKey(
        "apps.Restaurant", CASCADE, related_name="waiter_calls", verbose_name=_("Restoran")
    )
    table = ForeignKey(
        "apps.Table", CASCADE, related_name="waiter_calls", verbose_name=_("Stol")
    )
    order = ForeignKey(
        "apps.Order",
        SET_NULL,
        null=True,
        blank=True,
        related_name="waiter_calls",
        verbose_name=_("Buyurtma"),
        help_text=_("PAYMENT turi uchun - qaysi buyurtma to'lanmoqchi."),
    )
    call_type = CharField(_("Chaqiruv turi"), max_length=20, choices=CallType.choices)
    amount = DecimalField(
        _("To'lov summasi"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    status = CharField(_("Holati"), max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    resolved_at = DateTimeField(_("Bajarilgan vaqt"), null=True, blank=True)

    class Meta:
        verbose_name = _("Ofitsiant chaqiruvi")
        verbose_name_plural = _("Ofitsiant chaqiruvlari")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Stol {self.table.number} - {self.get_call_type_display()} ({self.get_status_display()})"