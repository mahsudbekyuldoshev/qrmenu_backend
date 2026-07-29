from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    Model,
    OneToOneField,
)
from django.db.models.enums import TextChoices
from django.utils import timezone

from apps.models.restaurants import Restaurant


class Subscription(Model):
    """
    Obuna modeli.
    Restoranlarning tarif rejalari va obuna holatlarini boshqarish uchun.

    Super Admin dashboard shu model orqali har bir restoranning trial/paid
    holatini va muddati tugashiga qancha kun qolganini ko'rsatadi.
    """

    class PlanType(TextChoices):
        TRIAL = "trial", "Sinov muddati (Trial)"
        PAID = "paid", "To'lov qilingan"

    restaurant = OneToOneField(
        Restaurant, CASCADE, related_name="subscription_info", verbose_name="Restoran"
    )
    plan_name = CharField(max_length=100, verbose_name="Tarif nomi")
    plan_type = CharField(
        max_length=20,
        choices=PlanType.choices,
        default=PlanType.TRIAL,
        verbose_name="Tarif turi",
    )
    is_active = BooleanField(default=True, verbose_name="Faol")
    start_date = DateTimeField(auto_now_add=True, verbose_name="Boshlanish vaqti")
    end_date = DateTimeField(verbose_name="Tugash vaqti")

    class Meta:
        verbose_name = "Obuna"
        verbose_name_plural = "Obunalar"

    def __str__(self):
        return f"{self.restaurant.name} - {self.plan_name} ({self.get_plan_type_display()})"

    @property
    def days_remaining(self) -> int:
        """Super Admin dashboardida 'muddati tugashiga N kun qoldi' ko'rsatish uchun."""
        delta = self.end_date - timezone.now()
        return max(delta.days, 0)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.end_date
