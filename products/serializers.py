from rest_framework import serializers
from .models import Category, Product, Cart, CartItem, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    class Meta:
        model = Category

        fields = ['id', 'name', 'slug', 'description']


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров"""

    reviews = serializers.ReadOnlyField()

    class Meta:
        model = Product

        fields = [
            'id', 
            'name', 
            'description', 
            'price', 
            'category', 
            'quantity', 
            'is_available', 
            'created_at',
            'reviews'
        ]
        
        read_only_fields = ['created_at']


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов корзины"""
    product_name = serializers.ReadOnlyField(source='product.name')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity', 'total_price']
        read_only_fields = ['id', 'product_name', 'total_price']

    def get_total_price(self, obj):
        # Берет сумму одной позиции
        return obj.get_total_price()

class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at']
        read_only_fields = ['user', 'total_price', 'created_at']

    def get_total_price(self, obj):
        # Берет общую сумму всей корзины
        return obj.get_total_price()

class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиции в заказе"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_price', 'items', 'created_at']
        read_only_fields = ['total_price', 'status']