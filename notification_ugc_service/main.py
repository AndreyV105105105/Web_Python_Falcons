import asyncio
from fastapi import FastAPI, BackgroundTasks
from .schemas import OrderNotificationPayload, NotificationResponse

# Инициализируем приложение FastAPI
app = FastAPI(title="Notification & UGC Service")

# ФОНОВЫЕ ЗАДАЧИ
async def send_email_notification(order_id: int, email: str, customer_name: str):
    """Имитация отправки email-уведомления"""
    print(f"\n[FASTAPI] >>> Начата фоновая обработка уведомления для заказа №{order_id}")
    print(f"[FASTAPI] >>> Подготовка письма для клиента: {customer_name} ({email})")

    # Имитируем реальную задержку
    await asyncio.sleep(5)

    print(f"[FASTAPI] <<< УСПЕХ: Письмо по заказу №{order_id} отправлено на адрес {email}!\n")


# ЭНДПОИНТЫ
@app.post("/notifications/new-order", response_model=NotificationResponse, status_code=202)
async def receive_order_notification(payload: OrderNotificationPayload, background_tasks: BackgroundTasks):
    """Эндпоинт-приемник событий о новом заказе из Django."""

    print(f"[FASTAPI] Получено уведомление от Django! Заказ №{payload.order_id}, Сумма: {payload.total_price}")

    # Добавляем задачу на отправку письма в очередь фоновых задач FastAPI
    background_tasks.add_task(
        send_email_notification,
        payload.order_id,
        payload.customer_email,
        payload.customer_name
    )

    # Возвращаем 202 Accepted
    return NotificationResponse(
        success=True,
        message=f"Уведомление для заказа {payload.order_id} принято. Обработка запущена в фоне."
    )


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "ok", "service": "notification_ugc"}