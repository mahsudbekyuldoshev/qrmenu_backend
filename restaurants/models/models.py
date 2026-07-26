from django.db import models
import uuid

class Restaurant(models.Model):
    """
    Restoran modeli.
    Tizimda har bir restoranning o'zining alohida sozlamalari, menyusi va stollari bo'ladi (SaaS modeli).
    """
    name = models.CharField(max_length=255, verbose_name="Restoran nomi")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug (URL uchun)")
    is_active = models.BooleanField(default=True, verbose_name="Aktivlik statusi")
    subscription_end_date = models.DateTimeField(verbose_name="Obuna tugash vaqti", null=True, blank=True)
    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_restaurants",
        verbose_name="Egasi",
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Restoran"
        verbose_name_plural = "Restoranlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Table(models.Model):
    """
    Stol modeli.
    Restorandagi stollar raqami yoki nomi va QR-kod uchun maxsus xavfsiz hashni saqlaydi.
    """
    restaurant = models.ForeignKey(
        Restaurant, 
        on_delete=models.CASCADE, 
        related_name="tables", 
        verbose_name="Restoran"
    )
    number = models.CharField(max_length=50, verbose_name="Stol raqami/nomi")
    qr_hash = models.CharField(
        max_length=64, 
        unique=True, 
        blank=True, 
        verbose_name="QR kod uchun hash"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktivlik statusi")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Stol"
        verbose_name_plural = "Stollar"
        unique_together = ("restaurant", "number")  # Bitta restoranda bir xil raqamli stol bo'lishi mumkin emas
        ordering = ["number"]

    def save(self, *args, **kwargs):
        # Stol yaratilayotganda qr_hash avtomatik ravishda UUID4 orqali generatsiya qilinadi
        if not self.qr_hash:
            self.qr_hash = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.restaurant.name} - Stol №{self.number}"


class Category(models.Model):
    """
    Kategoriya modeli.
    Taomlar guruhlarini boshqarish uchun (masalan: Suyuq taomlar, Salatlar, Ichimliklar).
    """
    restaurant = models.ForeignKey(
        Restaurant, 
        on_delete=models.CASCADE, 
        related_name="categories", 
        verbose_name="Restoran"
    )
    name = models.CharField(max_length=255, verbose_name="Kategoriya nomi")
    slug = models.SlugField(max_length=255, verbose_name="Slug (URL uchun)")
    description = models.TextField(blank=True, null=True, verbose_name="Kategoriya tavsifi")
    is_active = models.BooleanField(default=True, verbose_name="Faollik statusi")
    ordering = models.IntegerField(default=0, verbose_name="Tartib raqami (Saralash uchun)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        unique_together = ("restaurant", "slug")  # Bitta restoranda bir xil slugga ega kategoriya bo'lishi mumkin emas
        ordering = ["ordering", "name"]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class Dish(models.Model):
    """
    Taom modeli.
    Kategoriyaga tegishli bo'lgan taomlar haqida ma'lumotlarni saqlaydi.
    `is_available` maydoni stop-list vazifasini bajaradi (taom hozirda bormi yoki yo'qligini bildiradi).
    """
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="dishes", 
        verbose_name="Kategoriya"
    )
    name = models.CharField(max_length=255, verbose_name="Taom nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Taom tavsifi")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi")
    image = models.ImageField(upload_to="dishes/", blank=True, null=True, verbose_name="Taom rasmi")
    is_available = models.BooleanField(default=True, verbose_name="Mavjud (Stop-list)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan vaqt")

    class Meta:
        verbose_name = "Taom"
        verbose_name_plural = "Taomlar"
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.restaurant.name} - {self.name} ({self.price} so'm)"
