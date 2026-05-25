from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

class DomainError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class EmptyCartError(DomainError):
    pass

class NotEnoughStockError(DomainError):
    pass

def custom_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {
                'success': False,
                'status_code': 400,
                'message': 'Ошибка бизнес-логики',
                'details': {'error': str(exc)}
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'success': False,
            'status_code': response.status_code,
            'message': 'Произошла ошибка при обработке запроса',
            'details': response.data
        }
        response.data = custom_response_data

    return response