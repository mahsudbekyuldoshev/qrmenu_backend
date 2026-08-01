from decimal import Decimal

from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    OneToOneField,
    Sum,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Subscription(Model):
    """
    Obuna modeli.

    Platformada faqat BITTA tarif rejasi mavjud. Mantiq oddiy:

        Restoran obunaga ega (bog'langan Subscription mavjud) va u
        `is_active=True` hamda `end_date` hali o'tmagan bo'lsa - restoran
        platformaning BARCHA funksiyalaridan to'liq foydalanadi.

    `has_access` propertysi shu tekshiruvni bitta joyda markazlashtiradi -
    permission qatlamida ham aynan shu propertydan foydalaning.

    Obuna narxi/muddati Super Admin panel orqali o'zgartiriladi (uzaytirish =
    yangi `Payment` yozuvi + `end_date`ni surish, qarang: `Payment` modeli
    va `apps.serializers.admin`).
    """

    restaurant = OneToOneField(
        "apps.Restaurant",
        CASCADE,
        related_name="subscription_info",
        verbose_name=_("Restoran"),
    )
    price = DecimalField(
        _("Oylik narxi (so'm)"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("299000.00"),
        help_text=_("Barcha restoranlar uchun yagona tarif narxi."),
    )
    is_active = BooleanField(_("Faol"), default=True)
    start_date = DateTimeField(_("Boshlanish vaqti"), auto_now_add=True)
    end_date = DateTimeField(_("Tugash vaqti"))

    class Meta:
        verbose_name = _("Obuna")
        verbose_name_plural = _("Obunalar")

    def __str__(self):
        holat = _("Faol") if self.has_access else _("Muddati tugagan")
        return f"{self.restaurant.name} - {self.price} so'm/oy ({holat})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.end_date

    @property
    def days_remaining(self) -> int:
        """Super Admin dashboardida 'muddati tugashiga N kun qoldi' ko'rsatish uchun."""
        delta = self.end_date - timezone.now()
        return max(delta.days, 0)

    @property
    def has_access(self) -> bool:
        """
        Restoran platformadan foydalanishi mumkinmi - yagona haqiqat manbai.
        Permission klasslari (masalan IsRestaurantStaff) shu propertyni
        chaqirib restoranga kirishni cheklashi kerak.
        """
        return self.is_active and not self.is_expired

    @property
    def total_paid(self) -> Decimal:
        """Obuna boshlanganidan beri restoran qancha to'lov qilgani (Payment yig'indisi)."""
        result = self.payments.aggregate(total=Sum("amount"))["total"]
        return result or Decimal("0")


class Payment(Model):
    """
    To'lov tarixi.

    Har safar Super Admin restoran obunasini uzaytirsa/yangilasa, shu yerda
    yozuv qoladi - "restoran obuna bo'lgandan beri qancha to'lov qilgan"
    degan savolga javob shu jadval orqali beriladi (Subscription o'zi faqat
    JORIY holatni saqlaydi, tarixni emas).
    """

    subscription = ForeignKey(
        "apps.Subscription",
        CASCADE,
        related_name="payments",
        verbose_name=_("Obuna"),
    )
    amount = DecimalField(_("To'lov summasi (so'm)"), max_digits=12, decimal_places=2)
    period_months = DecimalField(
        _("Uzaytirilgan muddat (oy)"),
        max_digits=4,
        decimal_places=1,
        default=Decimal("1.0"),
    )
    note = CharField(_("Izoh"), max_length=255, blank=True)
    paid_at = DateTimeField(_("To'lov vaqti"), auto_now_add=True)

    class Meta:
        verbose_name = _("To'lov")
        verbose_name_plural = _("To'lovlar")
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.subscription.restaurant.name} - {self.amount} so'm ({self.paid_at:%Y-%m-%d})"