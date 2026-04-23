from django.db import transaction
from core.exceptions import EmptyCartError, NotEnoughStockError
from products.models import Cart, Order, OrderItem


def create_order_from_cart(user):
    """
    Бизнес-логика оформления заказа
    """
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        raise EmptyCartError("У вас нет корзины для оформления заказа.")

    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        raise EmptyCartError("Ваша корзина пуста, добавьте товары.")

    # Открываем транзакцию
    with transaction.atomic():
        total_price = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=user,
            status='new',
            total_price=total_price
        )

        order_items_to_create = []

        for item in cart_items:
            product = item.product

            # Проверка инвариантов
            if product.quantity < item.quantity:
                raise NotEnoughStockError(
                    f"Товар '{product.name}' закончился. В наличии: {product.quantity} шт."
                )

            product.quantity -= item.quantity
            product.save()

            order_items_to_create.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price_at_purchase=product.price
                )
            )

        OrderItem.objects.bulk_create(order_items_to_create)
        cart_items.delete()

    return order