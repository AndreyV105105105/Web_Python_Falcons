from database import db
from datetime import datetime, timezone

class Review(db.Model):
    """Модель отзыва"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, index=True)
    product_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        db.CheckConstraint("status IN ('active', 'hidden', 'pending')", name='check_status_values'),
        db.Index('idx_product_status', 'product_id', 'status'),
    )

    def to_dict(self):
        """Сериализация для API-ответа"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'rating': self.rating,
            'comment': self.comment,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }