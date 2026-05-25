import logging
from fastapi import FastAPI, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select, func
from datetime import datetime, timezone
import asyncio

from database import get_db, Base, async_engine
from models import Review, ProductRating
from schemas import (
    ReviewCreate, ReviewRead, ProductUGCResponse,
    OrderNotificationPayload, NotificationResponse
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(
    title='Notification & UGC Service',
    on_startup=[create_tables]
)


async def recalculate_product_rating_task(product_id: int):
    """
    Фоновая задача для пересчета среднего рейтинга товара.
    Использует атомарный UPSERT (ON CONFLICT DO UPDATE).
    """
    logger.info(f"Background rating recalculation started for product_id={product_id}")
    await asyncio.sleep(2)
    AsyncSessionLocal: sessionmaker = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        try:
            query = select(
                func.coalesce(func.avg(Review.rating), 0.0),
                func.count(Review.id)
            ).where(Review.product_id == product_id)

            result = await session.execute(query)
            avg_rating, reviews_count = result.fetchone()

            stmt = insert(ProductRating).values(
                product_id=product_id,
                average_rating=float(avg_rating),
                reviews_count=reviews_count,
                updated_at=datetime.now(timezone.utc)
            ).on_conflict_do_update(
                index_elements=['product_id'],
                set_={
                    'average_rating': float(avg_rating),
                    'reviews_count': reviews_count,
                    'updated_at': datetime.now(timezone.utc)
                }
            )

            await session.execute(stmt)
            await session.commit()
            logger.info(f"Rating updated for product_id={product_id}: avg={avg_rating}, count={reviews_count}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error calculating rating for product_id={product_id}: {e}")


async def send_email_notification(order_id: int, email: str, customer_name: str):
    """Имитация асинхронной отправки email-уведомления клиенту."""
    logger.info(f"Sending email notification for order {order_id} to {email}")
    await asyncio.sleep(3)
    logger.info(f"Email notification for order {order_id} successfully sent")


@app.post('/reviews/', response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
        review: ReviewCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """Создание нового отзыва с последующим фоновым пересчетом рейтинга."""
    logger.info(f"Creating review for product_id={review.product_id} by user_id={review.user_id}")

    db_review = Review(
        product_id=review.product_id,
        user_id=review.user_id,
        user_name=review.user_name,
        rating=review.rating,
        comment=review.comment,
        status="active"
    )

    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)

    background_tasks.add_task(recalculate_product_rating_task, review.product_id)
    return db_review


@app.get('/products/{product_id}/ugc', response_model=ProductUGCResponse)
async def get_product_ugc(product_id: int, db: AsyncSession = Depends(get_db)):
    """Получение агрегированного рейтинга товара и списка активных отзывов."""
    rating_query = select(ProductRating).where(ProductRating.product_id == product_id)
    rating_result = await db.execute(rating_query)
    product_rating = rating_result.scalar_one_or_none()

    reviews_query = select(Review).where(
        Review.product_id == product_id,
        Review.status == "active"
    ).order_by(Review.created_at.desc())
    reviews_result = await db.execute(reviews_query)
    reviews_list = reviews_result.scalars().all()

    return ProductUGCResponse(
        product_id=product_id,
        average_rating=product_rating.average_rating if product_rating else 0.0,
        reviews_count=product_rating.reviews_count if product_rating else 0,
        reviews=reviews_list
    )


@app.post("/notifications/new-order", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_order_notification(payload: OrderNotificationPayload, background_tasks: BackgroundTasks):
    """Приемник вебхуков от Django для постановки задачи отправки уведомлений в очередь."""
    logger.info(f"Received order notification from Django. Order ID: {payload.order_id}")

    background_tasks.add_task(
        send_email_notification,
        payload.order_id,
        payload.customer_email,
        payload.customer_name
    )

    return NotificationResponse(
        success=True,
        message=f"Order {payload.order_id} notification accepted for background processing"
    )