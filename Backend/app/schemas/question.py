from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuestionBase(BaseModel):
    axis_id: int
    category_id: Optional[int] = None
    question_text: str
    theme: Optional[str] = None
    order_index: Optional[int] = 1
    max_score: Optional[int] = 5
    is_active: Optional[bool] = True

    target_less_than_10: Optional[bool] = True
    target_11_to_50: Optional[bool] = True
    target_more_than_50: Optional[bool] = True


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    axis_id: Optional[int] = None
    category_id: Optional[int] = None
    question_text: Optional[str] = None
    theme: Optional[str] = None
    order_index: Optional[int] = None
    max_score: Optional[int] = None
    is_active: Optional[bool] = None

    target_less_than_10: Optional[bool] = None
    target_11_to_50: Optional[bool] = None
    target_more_than_50: Optional[bool] = None


class QuestionRead(QuestionBase):
    id: int
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminQuestionRead(QuestionRead):
    axis_name: str
    axis_order_index: int
    category_name: Optional[str] = None
    category_order_index: Optional[int] = None

class ReorderAxisQuestionsRequest(BaseModel):
    category_id: Optional[int] = None
    ordered_question_ids: list[int]