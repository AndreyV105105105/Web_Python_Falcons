from django.db import models
from django.db.models import CheckConstraint, Q
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Категория товаров (для фильтрации)"""
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории",
        db_index=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL-адрес (slug)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание категории"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар магазина"""
    name = models.CharField(
        max_length=200,
        verbose_name="Название товара",
        db_index=True
    )
    description = models.TextField(
        verbose_name="Описание товара"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        validators=[MinValueValidator(0)]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Категория"
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество на складе"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="В наличии"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

        constraints = [
            CheckConstraint(
                condition=Q(price__gte=0),
                name='product_price_non_negative'
            ),
            CheckConstraint(
                condition=Q(quantity__gte=0),
                name='product_quantity_non_negative'
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.price} ₽"


class Cart(models.Model):
    """Корзина пользователя"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="Пользователь"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.user.username}"

    def get_total_price(self):
        """Считает общую сумму товаров в корзине"""
        return sum(item.get_total_price() for item in self.items.all())


class CartItem(models.Model):
    """Позиция в корзине"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Корзина"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = [['cart', 'product']]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_total_price(self):
        """Сумма за эту позицию"""
        return self.product.price * self.quantity


class Order(models.Model):
    """Заказ пользователя"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Пользователь"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итоговая сумма"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата заказа"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

        constraints = [
            CheckConstraint(
                condition=Q(total_price__gte=0),
                name='order_total_price_non_negative'
            ),
        ]

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"


class OrderItem(models.Model):
    """Позиция в заказе (история покупки)"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество"
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена на момент покупки"
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

        constraints = [
            CheckConstraint(
                condition=Q(quantity__gt=0),
                name='orderitem_quantity_positive'
            ),
            CheckConstraint(
                condition=Q(price_at_purchase__gte=0),
                name='orderitem_price_non_negative'
            ),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_total_price(self):
        """Сумма за эту позицию в заказе"""
        return self.price_at_purchase * self.quantity