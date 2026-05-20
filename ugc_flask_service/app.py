import os
from flask import Flask, jsonify
from errors import register_error_handlers, APIError # Импортируем наши обработчики

app = Flask(__name__)

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