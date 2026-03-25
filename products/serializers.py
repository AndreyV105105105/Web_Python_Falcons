from rest_framework import serializers
from .models import Category, Product, Cart, CartItem, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    class Meta:
        model = Category
        
        fields = ['id', 'name', 'slug', 'description']


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров"""
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
            'created_at'
        ]
        
        read_only_fields = ['created_at']


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов корзины"""
    product_name = serializers.ReadOnlyField(source='product.name')
    total_price = serializers.ReadOnlyField(method='get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'quantity', 'total_price']

    def validate(self, data):
        """Проверка наличия товара на складе"""
        product = data['product']
        quantity = data['quantity']
        if product.quantity < quantity:
            raise serializers.ValidationError(
                f"Недостаточно товара {product.name} на складе. В наличии: {product.quantity}"
            )
        return data

class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField(source='get_total_price')

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at']

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