from fastapi import FastAPI, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime, timezone
import asyncio

from .database import get_db, AsyncSessionLocal, Base, async_engine
from .models import Review, ProductRating
from .schemas import (
    ReviewCreate, ReviewRead, ProductUGCResponse,
    OrderNotificationPayload, NotificationResponse
)

async def create_tables():
    """Создаём таблицы при старте"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Инициализируем приложение FastAPI
app = FastAPI(
    title="Notification & UGC Service",
    on_startup=[create_tables]
)


@app.post("/reviews/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
        review: ReviewCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """Создать отзыв + запустить пересчёт рейтинга в фоне"""

    db_review = Review(
        product_id=review.product_id,
        user_id=review.user_id,
        user_name=f"User_{review.user_id}",
        rating=review.rating,
        comment=review.comment,
        status="active",
        created_at=datetime.now(timezone.utc)
    )

    db.add(db_review)
    await db.flush()
    await db.refresh(db_review)

    # Запускаем пересчёт рейтинга в фоне
    background_tasks.add_task(recalculate_product_rating, review.product_id)

    return db_review


@app.get("/products/{product_id}/reviews", response_model=ProductUGCResponse)
async def get_product_reviews(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Получить все отзывы товара"""

    reviews_stmt = select(Review).where(
        Review.product_id == product_id,
        Review.status == "active"
    ).order_by(Review.created_at.desc())

    result = await db.execute(reviews_stmt)
    reviews = result.scalars().all()

    rating_stmt = select(ProductRating).where(
        ProductRating.product_id == product_id
    )
    rating_result = await db.execute(rating_stmt)
    cached_rating = rating_result.scalar_one_or_none()

    if cached_rating:
        avg_rating = cached_rating.average_rating
        count = cached_rating.reviews_count
    else:
        avg_result = await db.execute(
            select(func.avg(Review.rating)).where(
                Review.product_id == product_id,
                Review.status == "active"
            )
        )
        avg_rating = avg_result.scalar() or 0.0
        count = len(reviews)

    return ProductUGCResponse(
        product_id=product_id,
        average_rating=round(avg_rating, 2),
        reviews_count=count,
        reviews=[ReviewRead.model_validate(r) for r in reviews]
    )


async def recalculate_product_rating(product_id: int):
    """Фоновая задача: пересчитать средний рейтинг"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                func.avg(Review.rating),
                func.count(Review.id)
            ).where(
                Review.product_id == product_id,
                Review.status == "active"
            )
        )
        avg_rating, count = result.first()
        avg_rating = avg_rating or 0.0

        await db.execute(
            update(ProductRating)
            .where(ProductRating.product_id == product_id)
            .values(
                average_rating=avg_rating,
                reviews_count=count,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()




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