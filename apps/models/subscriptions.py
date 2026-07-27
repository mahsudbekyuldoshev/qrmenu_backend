from django.db import models
from django.db.models import Model, OneToOneField, CASCADE, CharField, BooleanField, DateTimeField

from apps.models.restaurants import Restaurant

class Subscription(Model):
    """
    Obuna modeli.
    Restoranlarning tarif rejalari va obuna holatlarini boshqarish uchun.
    """
    restaurant = OneToOneField(
        Restaurant, 
        CASCADE,
        related_name="subscription_info",
        verbose_name="Restoran"
    )
    plan_name = CharField(max_length=100, verbose_name="Tarif nomi")
    is_active = BooleanField(default=True, verbose_name="Faol")
    start_date = DateTimeField(auto_now_add=True, verbose_name="Boshlanish vaqti")
    end_date = DateTimeField(verbose_name="Tugash vaqti")

    class Meta:
        verbose_name = "Obuna"
        verbose_name_plural = "Obunalar"

    def __str__(self):
        return f"{self.restaurant.name} - {self.plan_name}"
