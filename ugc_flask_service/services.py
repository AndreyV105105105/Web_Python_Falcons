import os
import httpx
import logging
from models import Review
from database import db
from errors import APIError

logger = logging.getLogger(__name__)

DJANGO_URL = os.getenv("DJANGO_URL", "http://django-web:8000")

def check_product_exists_in_django(product_id: int):
    """Внутренний S2S запрос в Django для проверки существования товара"""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f'{DJANGO_URL}/api/products/{product_id}/')

            if response.status_code == 404:
                raise APIError(
                    message='Товар не найден',
                    status_code=404,
                    details={'product_id': product_id}
                )
            # Если Django ответил что-то кроме 200 и 404
            elif response.status_code != 200:
                raise APIError(
                    message='Ошибка внешней системы при проверке товара',
                    status_code=502,
                    details={'django_status': response.status_code}
                )
    except httpx.RequestError as e:
        logger.error(f'Не удалось связаться с Django для проверки товара {product_id}: {e}')
        raise APIError(
            message='Сервис каталога временно недоступен',
            status_code=503
        )

def create_review_service(product_id: int, user_id: int, user_name: str, rating: int, comment: str) -> Review:
    # Интеграционная проверка товара
    check_product_exists_in_django(product_id)

    new_review = Review(
        product_id=product_id,
        user_id=user_id,
        user_name=user_name,
        rating=rating,
        comment=comment,
        status='pending' 
    )

    try:
        db.session.add(new_review)
        db.session.commit()
        logger.info(f'Создан отзыв #{new_review.id} для товара #{new_review.product_id}')
        return new_review
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка сохранения отзыва: {e}')
        raise APIError(message='Ошибка сохранения данных', status_code=500)

def update_review_status_service(review_id: int, new_status: str) -> Review:
    """Функция модерации (меняет статус отзыва в БД)"""
    allowed_statuses = ['active', 'hidden', 'pending']
    if new_status not in allowed_statuses:
        raise APIError(
            message='Недопустимый статус модерации',
            status_code=400,
            details={'allowed_statuses': allowed_statuses}
        )

    review = Review.query.get(review_id)
    if not review:
        raise APIError(
            message='Отзыв не найден',
            status_code=404,
            details={'review_id': review_id}
        )

    try:
        review.status = new_status
        db.session.commit()
        logger.info(f'Статус отзыва #{review_id} изменен на {new_status}')
        return review
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при обновлении статуса отзыва #{review_id}: {e}')
        raise APIError(message='Ошибка обновления данных модерации', status_code=500)