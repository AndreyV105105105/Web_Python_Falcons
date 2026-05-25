from rest_framework.exceptions import ValidationError
from products.models import CartItem

def add_item_to_cart(cart, product, quantity):
    """Бизнес-логика добавления товара в корзину"""
    if product.quantity < quantity:
        raise ValidationError(
            f"Недостаточно товара {product.name} на складе. В наличии: {product.quantity}"
        )

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    return item