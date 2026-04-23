from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from .selectors import get_product_list, get_category_list, get_user_cart_with_items, get_user_orders

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
        эндпоинт для оформления заказа из корзины.
        """
        user = request.user

        # Ищем корзину
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise ValidationError({"detail": "У вас нет корзины."})

        # Берем все товары в корзине
        cart_items = cart.items.select_related('product').all()

        if not cart_items.exists():
            raise ValidationError({"detail": "Ваша корзина пуста."})

        # 2. открываем транзакцию
        with transaction.atomic():

            # Считаем общую сумму заказа
            total_price = sum(item.product.price * item.quantity for item in cart_items)

            # Создаем заказ
            order = Order.objects.create(
                user=user,
                status='new',
                total_price=total_price
            )

            # Переносим товары из корзины в заказ и списываем со склада
            order_items_to_create = []

            for item in cart_items:
                product = item.product

                if product.quantity < item.quantity:
                    raise ValidationError(
                        {"detail": f"Товар {product.name} закончился. В наличии: {product.quantity}"}
                    )

                # Списываем товар со склада
                product.quantity -= item.quantity
                product.save()

                # Подготавливаем историю цены
                order_items_to_create.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=item.quantity,
                        price_at_purchase=product.price
                    )
                )

            # Сохраняем все позиции заказа разом
            OrderItem.objects.bulk_create(order_items_to_create)

            # Очищаем корзину
            cart_items.delete()

        # Отдаем клиенту ответ с его новым заказом
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)