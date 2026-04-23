from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

class DomainError(Exception):
    """Базовый класс для всех бизнес-ошибок"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class EmptyCartError(DomainError):
    """Вызывается, когда пытаются оформить пустую или несуществующую корзину"""
    pass

class NotEnoughStockError(DomainError):
    """Вызывается, когда на складе не хватает товара"""
    pass


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений.
    """
    # Ловим кастомные доменные ошибки с сервисов
    if isinstance(exc, DomainError):
        return Response(
            {
                'success': False,
                'status_code': 400,
                'message': 'Ошибка бизнес-логики',
                'details': {
                    'error': str(exc)
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Если это не наша ошибка, отдаем ее стандартному обработчику DRF
    response = exception_handler(exc, context)

    # Оборачиваем ошибки DRF
    if response is not None:
        custom_response_data = {
            'success': False,
            'status_code': response.status_code,
            'message': 'Произошла ошибка при обработке запроса',
            'details': response.data
        }
        response.data = custom_response_data

    return response