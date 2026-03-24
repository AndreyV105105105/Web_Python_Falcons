from rest_framework import serializers
from .models import Category, Product

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