from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройки админки для категорий"""
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Настройки админки для товаров"""
    list_display = ['name', 'price', 'category', 'quantity', 'is_available', 'created_at']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'quantity']
    raw_id_fields = ['category']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Настройки админки для корзин"""
    list_display = ['user', 'created_at']
    search_fields = ['user__username']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Настройки админки для товаров в корзине"""
    list_display = ['cart', 'product', 'quantity']
    raw_id_fields = ['cart', 'product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Настройки админки для заказов"""
    list_display = ['id', 'user', 'status', 'total_price', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'id']
    readonly_fields = ['total_price', 'created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Настройки админки для товаров в заказе"""
    list_display = ['order', 'product', 'quantity', 'price_at_purchase']
    raw_id_fields = ['order', 'product']