# python manage.py test products.tests.test_services


from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category, Cart, CartItem
from products.services.cart_services import add_item_to_cart
from products.services.order_service import create_order_from_cart
from core.exceptions import EmptyCartError, NotEnoughStockError

User = get_user_model()


class AddItemToCartServiceTest(TestCase):
    """Тесты на сервис 'добавление товара в корзину' """

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            name="MacBook",
            price=200000,
            category=self.category,
            quantity=5
        )
        self.cart, _ = Cart.objects.get_or_create(user=self.user)

    def test_add_item_success(self):
        """Успешное добавление товара в корзину"""
        result = add_item_to_cart(self.cart, self.product, quantity=5)

        self.assertEqual(result.quantity, 5)
        self.assertEqual(self.cart.items.count(), 1)

    def test_add_item_not_enough_stock(self):
        """Ошибка - недостаточно товара на складе"""
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            add_item_to_cart(self.cart, self.product, quantity=10)


    def test_add_item_updates_existing_cart_item(self):
        """Если товар уже в корзине, количество должно суммироваться"""
        # Сначала добавляем 2 товара
        add_item_to_cart(self.cart, self.product, quantity=2)

        # Добавляем ещё 3 таких же товара
        result = add_item_to_cart(self.cart, self.product, quantity=3)

        # Должен обновиться существующий CartItem, а не создаться новый
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(result.quantity, 5)


class CreateOrderFromCartServiceTest(TestCase):
    """Тесты на сервис 'оформление заказа' """

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            name="Xiaomi 67",
            price=100000,
            category=self.category,
            quantity=10
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_create_order_success(self):
        """Успешное оформление заказа"""
        order = create_order_from_cart(self.user)

        self.assertEqual(order.status, 'new')
        self.assertEqual(order.total_price, 200000)
        self.assertEqual(order.items.count(), 1)

        # Количество товара на складе должно уменьшиться
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 8)

        # Корзина должна автоматически очиститься
        self.assertEqual(self.cart.items.count(), 0)

    def test_create_order_empty_cart(self):
        """Ошибка - корзина пуста"""

        # Очищаем корзину
        self.cart.items.all().delete()

        with self.assertRaises(EmptyCartError):
            create_order_from_cart(self.user)

    def test_create_order_not_enough_stock(self):
        """Ошибка - недостаточно товара на складе"""

        # Уменьшаем количество на складе до 1
        self.product.quantity = 1
        self.product.save()

        with self.assertRaises(NotEnoughStockError):
            create_order_from_cart(self.user)

    def test_create_order_with_multiple_products(self):
        """Заказ с несколькими разными товарами"""

        # Сначала очищаем корзину от товара из setUp()
        self.cart.items.all().delete()

        # Создаём второй товар
        product2 = Product.objects.create(
            name="iPhone 15",
            price=150000,
            category=self.category,
            quantity=5
        )

        # Добавляем оба товара в корзину
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=self.cart, product=product2, quantity=1)

        # Оформляем заказ
        order = create_order_from_cart(self.user)

        # Проверяем сумму (должно быть 350000)
        self.assertEqual(order.total_price, 350000)
        self.assertEqual(order.items.count(), 2)

        # Проверяем, что оба товара уменьшились на складе
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(self.product.quantity, 8)
        self.assertEqual(product2.quantity, 4)


    def test_create_order_without_cart(self):
        """Ошибка - попытка оформить заказ без корзины"""
        # Создаём пользователя без корзины
        user_without_cart = User.objects.create_user(username='nolcart', password='test')

        with self.assertRaises(EmptyCartError):
            create_order_from_cart(user_without_cart)