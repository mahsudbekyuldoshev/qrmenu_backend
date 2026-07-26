from django.contrib import admin
from .models.models import Restaurant, Table, Category, Dish

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'subscription_end_date', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'restaurant', 'qr_hash', 'is_active')
    search_fields = ('number', 'qr_hash', 'restaurant__name')
    list_filter = ('restaurant', 'is_active')
    readonly_fields = ('qr_hash',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'ordering', 'is_active')
    search_fields = ('name', 'restaurant__name')
    list_filter = ('restaurant', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


class DishAdminInline(admin.TabularInline):
    model = Dish
    extra = 1

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    search_fields = ('name', 'category__name', 'category__restaurant__name')
    list_filter = ('category__restaurant', 'category', 'is_available')
