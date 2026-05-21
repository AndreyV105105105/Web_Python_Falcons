from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional


class ReviewCreate(BaseModel):
    """Схема для создания отзыва"""
    product_id: int = Field(..., gt=0, description="ID товара из Django")
    user_id: int = Field(..., gt=0, description="ID пользователя из Django")
    user_name: str = Field(..., min_length=2, max_length=100, description="Имя пользователя")
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    comment: str = Field(..., min_length=10, max_length=2000, description="Текст отзыва")

    @field_validator('comment')
    @classmethod
    def comment_not_empty_after_strip(cls, v: str) -> str:
        """Проверка: комментарий не должен состоять только из пробелов"""
        if not v.strip():
            raise ValueError('Комментарий не может состоять только из пробелов')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "user_id": 42,
                "user_name": "Иван Иванов",
                "rating": 5,
                "comment": "Отличный товар! Быстрая доставка, качественная упаковка."
            }
        }


class ReviewResponse(BaseModel):
    """Схема ответа с отзывом"""
    id: int
    product_id: int
    user_id: int
    user_name: str
    rating: int
    comment: str
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True