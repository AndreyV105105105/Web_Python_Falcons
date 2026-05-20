from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """Базовый класс для кастомных бизнес-ошибок сервиса UGC"""

    def __init__(self, message, status_code=400, details=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def register_error_handlers(app):
    """Регистрация глобальных обработчиков ошибок для Flask-приложения"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Перехват кастомных бизнес-ошибок"""
        response = {
            "success": False,
            "status_code": error.status_code,
            "message": error.message,
            "details": error.details
        }
        return jsonify(response), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Перехват стандартных ошибок Flask"""
        response = {
            "success": False,
            "status_code": error.code,
            "message": error.name,
            "details": {"error": error.description}
        }
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Перехват любых других серверных ошибок"""
        response = {
            "success": False,
            "status_code": 500,
            "message": "Внутренняя ошибка сервера",
            "details": {"error": str(error)}
        }
        return jsonify(response), 500