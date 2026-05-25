import os
from flask import Flask, jsonify, request
from errors import register_error_handlers, APIError

from schemas import ReviewCreate, ReviewResponse
from services import create_review_service, update_review_status_service
from pydantic import ValidationError
from models import Review
from database import init_db

app = Flask(__name__)

init_db(app)

register_error_handlers(app)

DJANGO_URL = os.getenv("DJANGO_URL", "http://django-web:8000")
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

    new_review = create_review_service(
        product_id=review_data.product_id,
        user_id=review_data.user_id,
        user_name=review_data.user_name,
        rating=review_data.rating,
        comment=review_data.comment
    )

    return jsonify(ReviewResponse.model_validate(new_review).model_dump()), 201


@app.route('/api/v1/ugc/reviews/<int:review_id>/moderate', methods=['PATCH'])
def moderate_review(review_id: int):
    """Эндпоинт для изменения статуса модерации отзыва администратором"""
    data = request.get_json(force=True, silent=True)

    if not data or 'status' not in data:
        raise APIError(
            message='Отсутствует обязательное поле status',
            status_code=400
        )

    new_status = data['status']
    updated_review = update_review_status_service(review_id=review_id, new_status=new_status)

    return jsonify({
        'success': True,
        'message': f'Статус отзыва #{review_id} успешно изменен',
        'review': updated_review.to_dict()
    }), 200


@app.route('/api/v1/ugc/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id: int):
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