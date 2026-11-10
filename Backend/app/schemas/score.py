from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)