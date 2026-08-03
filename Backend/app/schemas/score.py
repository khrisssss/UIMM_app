from pydantic import BaseModel
from datetime import datetime


class ScoreRead(BaseModel):
    id: int
    company_id: int
    axis_id: int
    score_total: int
    score_max: int
    score_percentage: float
    answered_questions: int
    total_questions: int
    calculated_at: datetime

    class Config:
        from_attributes = True