import httpx
import logging
from django.db import transaction
from core.exceptions import EmptyCartError, NotEnoughStockError
from products.models import Cart, Order, OrderItem

logger = logging.getLogger(__name__)

def create_order_from_cart(user):
    """Бизнес-логика оформления заказа с последующим уведомлением микросервиса"""
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        raise EmptyCartError("У вас нет корзины для оформления заказа.")

    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        raise EmptyCartError("Ваша корзина пуста, добавьте товары.")

    # Основная логика создания заказа
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

            # Проверка наличия на складе
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

    # Формируем список товаров для уведомления
    items_payload = [
        {
            "product_name": item.product.name,
            "quantity": item.quantity,
            "price": float(item.price_at_purchase)
        } for item in order_items_to_create
    ]

    notification_data = {
        "order_id": order.id,
        "customer_email": user.email,
        "customer_name": user.username,
        "total_price": float(order.total_price),
        "items": items_payload,
        "created_at": order.created_at.isoformat() if hasattr(order, 'created_at') else None
    }

    try:
        # Отправляем POST запрос в микросервис
        response = httpx.post(
            "http://fastapi_service:8001/notifications/new-order",
            json=notification_data,
            timeout=5.0
        )
        response.raise_for_status()

        logger.info(f"Успешно отправлено уведомление в FastAPI для заказа №{order.id}")

    except Exception as e:
        # Логируем ошибку, но не прерываем работу Django, так как заказ в БД уже создан
        logger.error(f"Ошибка при отправке уведомления в FastAPI для заказа №{order.id}: {e}")

    return order