from django.contrib import admin
from apps.models.orders import Order, OrderItem
from apps.models.restaurants import Restaurant, Table, Category, Dish
from apps.models.subscriptions import Subscription

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


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurant', 'table', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'restaurant', 'created_at')
    search_fields = ('id', 'restaurant__name', 'table__number')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    fieldsets = (
        (None, {
            'fields': ('restaurant', 'table', 'status', 'total_price')
        }),
        ('Qo\'shimcha', {
            'fields': ('comment', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'dish', 'quantity', 'price')
    list_filter = ('order__restaurant',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'plan_name', 'is_active', 'end_date')
    list_filter = ('is_active', 'plan_name')
    search_fields = ('restaurant__name', 'plan_name')
