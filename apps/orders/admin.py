from django.contrib import admin
from .models.models import Order, OrderItem

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
