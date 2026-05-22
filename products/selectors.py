import httpx
import logging
from django.db.models import Prefetch
from .models import Product, Category, Cart, Order, CartItem

logger = logging.getLogger(__name__)

def get_product_list(filters=None):
    """Селектор для получения списка товаров с фильтрацией"""
    queryset = Product.objects.select_related('category').all()

    if filters:
        if filters.get('category'):
            queryset = queryset.filter(category_id=filters['category'])
        if filters.get('is_available'):
            queryset = queryset.filter(is_available=True)
        if filters.get('min_price'):
            queryset = queryset.filter(price__gte=filters['min_price'])
        if filters.get('max_price'):
            queryset = queryset.filter(price__lte=filters['max_price'])

    return queryset

def get_product_reviews(product_id):
    """Функция для получения отзывов из FastAPI"""

    try:
        response = httpx.get(
            f'http://flask-ugc-service:8002/api/v1/ugc/products/{product_id}/reviews',
            params={'status': 'active'},
            timeout=2.0
        )

        response.raise_for_status()
        data = response.json()

        return data.get('reviews', [])
    
    except httpx.RequestError as e:
        logging.error(f'Ошибка при запросе отзывов для товара {product_id}: {e}')
        return []
    except httpx.HTTPStatusError as e:
        logging.error(f'Неверный ответ при запросе отзывов для товара {product_id}: {e}')
        return []

def get_product_by_id(product_id):
    """Получаем один товар по ID"""
    
    product = Product.objects.select_related('category').get(id=product_id)
    reviews = get_product_reviews(product_id)
    product.reviews = reviews

    return product

def get_category_list():
    """Получаем список категорий"""
    return Category.objects.all()


def get_user_cart_with_items(user):
    """Получаем корзину пользователя с товарами"""
    return Cart.objects.select_related('user').prefetch_related(
        Prefetch('items', queryset=CartItem.objects.select_related('product'))
    ).get(user=user)


def get_user_orders(user):
    """Получаем все заказы пользователя"""
    return Order.objects.select_related('user').prefetch_related(
        'items'
    ).filter(user=user).order_by('-created_at')


def get_order_by_id_with_items(order_id):
    """Получаем заказ с позициями"""
    return Order.objects.select_related('user').prefetch_related(
        'items'
    ).get(id=order_id)