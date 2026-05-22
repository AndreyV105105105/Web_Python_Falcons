import os
from flask import Flask, jsonify, request
from errors import register_error_handlers, APIError # Импортируем наши обработчики

from schemas import ReviewCreate, ReviewResponse
from services import create_review_service
from pydantic import ValidationError
from models import Review, db
from database import init_db
import httpx

app = Flask(__name__)

init_db(app)

register_error_handlers(app)

DJANGO_URL = os.getenv("DJANGO_URL", "http://django_web:8000")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi_service:8001")

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Эндпоинт для проверки работоспособности сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "flask-ugc-service",
        "integrations": {
            "django_url": DJANGO_URL,
            "fastapi_url": FASTAPI_URL
        }
    }), 200


@app.route('/api/v1/ugc/reviews/', methods=['POST'])
@app.route('/api/v1/ugc/', methods=['POST'])
def create_review():
    """Создание отзыва с валидацией и проверкой товара в Django"""

    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            raise APIError(message='Неверный формат JSON', status_code=400)
        review_data = ReviewCreate(**data)
    except ValidationError as e:
        errors = {err['loc'][0]: err['msg'] for err in e.errors()}
        raise APIError(
            message='Ошибка валидации данных',
            status_code=400,
            details=errors
        )

    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f'{DJANGO_URL}/api/products/{review_data.product_id}/')
            if response.status_code == 404:
                raise APIError(
                    message='Товар не найден',
                    status_code=404,
                    details={'product_id': review_data.product_id}
                )
    except httpx.RequestError as e:
        app.logger.warning(f'Не удалось проверить товар {review_data.product_id} в Django: {e}')

    new_review = create_review_service(
        product_id=review_data.product_id,
        user_id=review_data.user_id,
        user_name=review_data.user_name,
        rating=review_data.rating,
        comment=review_data.comment
    )

    return jsonify(ReviewResponse.model_validate(new_review).model_dump()), 201


@app.route('/api/v1/ugc/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id: int):
    """Получение активных отзывов для товара"""
    status_filter = request.args.get('status', 'active')

    reviews = Review.query.filter_by(
        product_id=product_id,
        status=status_filter
    ).order_by(Review.created_at.desc()).all()

    return jsonify({
        'product_id': product_id,
        'status_filter': status_filter,
        'count': len(reviews),
        'reviews': [r.to_dict() for r in reviews]
    }), 200


# Тестовый эндпоинт, чтобы проверить, как работает отлов кастомных ошибок
@app.route('/api/v1/test-error', methods=['GET'])
def test_error():
    raise APIError(
        message="Ошибка бизнес-логики: неверный формат отзыва",
        status_code=422,
        details={"rating": "Рейтинг должен быть числом от 1 до 5"}
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)