from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cart, CartItem, Order
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from .selectors import get_product_by_id, get_product_list, get_category_list, get_user_cart_with_items, get_user_orders

from products.services.order_service import create_order_from_cart
from products.services.cart_services import add_item_to_cart

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для категорий"""

    def get_queryset(self):
        return get_category_list()
    
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для товаров"""

    def get_queryset(self):
        return get_product_list()
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_product_by_id(pk) 
    
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
    # только для авторизованных пользователей
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        quantity = int(quantity)
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        serializer.instance = add_item_to_cart(cart=cart, product=product, quantity=quantity)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для управления заказами"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # только для авторизованных пользователей
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