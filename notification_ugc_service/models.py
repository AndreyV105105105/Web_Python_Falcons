from sqlalchemy import Column, Integer, String, Float, Text, DateTime, CheckConstraint
from datetime import datetime, timezone
from .database import Base


class Review(Base):
    """Модель отзыва (UGC)"""
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint("status IN ('active', 'hidden', 'pending')", name='check_status_values'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProductRating(Base):
    """Кэшированный средний рейтинг товара (для быстрого доступа)"""
    __tablename__ = "product_ratings"

    product_id = Column(Integer, primary_key=True, index=True)
    average_rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))