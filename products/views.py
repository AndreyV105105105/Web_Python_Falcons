from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from .selectors import get_product_list, get_category_list, get_user_cart_with_items, get_user_orders

from products.services.order_service import create_order_from_cart

from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from django.db import transaction

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для категорий"""

    def get_queryset(self):
        return get_category_list()
    
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для товаров"""

    def get_queryset(self):
        return get_product_list()
    
    serializer_class = ProductSerializer
    
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter, 
        filters.OrderingFilter
    ]
    
    filterset_fields = ['category', 'is_available', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    

class CartViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра корзины"""

    def get_queryset(self):
        return get_user_cart_with_items(user=self.request.user)
    
    serializer_class = CartSerializer

class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet для управления позициями в корзине"""
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    # Доступ только для авторизованных
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свою корзину
        return get_user_cart_with_items(user=self.request.user)

    def perform_create(self, serializer):
        # Автоматическая привязка корзины
        # Ищем корзину текущего пользователя, или создаем, если её нет
        cart, created = Cart.objects.get_or_create(user=self.request.user)

        product = serializer.validated_data['product']

        # Проверяем, нет ли уже этого товара в корзине
        if CartItem.objects.filter(cart=cart, product=product).exists():
            raise ValidationError({"detail": "Этот товар уже есть в вашей корзине."})

        # Сохраняем товар, привязывая его к найденной корзине
        serializer.save(cart=cart)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для управления заказами"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # только для авторизованных
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои заказы
        return get_user_orders(user=self.request.user)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        Эндпоинт для оформления заказа.
        """
        # Вызываем сервис
        order = create_order_from_cart(user=request.user)

        # Упаковываем готовый ответ
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)