from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AnswerCreate(BaseModel):
    question_id: int
    score_code: Optional[str] = None
    answer_text: Optional[str] = None
    comment: Optional[str] = None


class AnswerRead(BaseModel):
    id: int
    company_id: int
    question_id: int
    score_code: Optional[str] = None
    score_value: Optional[int] = None
    answer_text: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)