from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений.
    """

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