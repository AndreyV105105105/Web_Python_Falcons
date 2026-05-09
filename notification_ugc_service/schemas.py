from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# UGC СХЕМЫ

class ReviewBase(BaseModel):
    """Базовая схема отзыва"""
    product_id: int = Field(..., description="ID товара из основной БД Django")
    user_id: int = Field(..., description="ID пользователя из основной БД Django")
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    comment: str = Field(..., min_length=5, max_length=1000, description="Текст отзыва")

class ReviewCreate(ReviewBase):
    """Схема для создания отзыва"""
    pass

class ReviewRead(ReviewBase):
    """Схема для чтения отзыва"""
    id: int
    user_id: int
    user_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProductUGCResponse(BaseModel):
    """Сводная информация по отзывам товара"""
    product_id: int
    average_rating: float = Field(0.0, ge=0, le=5)
    reviews_count: int
    reviews: List[ReviewRead]


# СХЕМЫ УВЕДОМЛЕНИЙ

class OrderItemSchema(BaseModel):
    """Позиция в заказе для уведомления"""
    product_name: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0)

class OrderNotificationPayload(BaseModel):
    """Данные для отправки уведомления о новом заказе"""
    order_id: int
    customer_email: EmailStr
    customer_name: str
    total_price: float = Field(..., ge=0)
    items: List[OrderItemSchema]
    created_at: datetime = Field(default_factory=datetime.now)

class NotificationResponse(BaseModel):
    """Ответ сервиса на принятие уведомления"""
    success: bool
    message: str
    task_id: Optional[str] = None