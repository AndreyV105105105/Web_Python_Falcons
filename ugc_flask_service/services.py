from models import db, Review
from errors import APIError
import logging

logger = logging.getLogger(__name__)

def create_review_service(product_id: int, user_id: int, user_name: str, rating: int, comment: str) -> Review:
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
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка сохранения отзыва: {e}')
        raise APIError(message='Ошибка сохранения данных', status_code=500)