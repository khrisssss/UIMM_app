from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SWOTAxisScoreContext(BaseModel):
    axis_id: int
    axis_name: str
    score_total: int
    score_max: int
    score_percentage: float
    answered_questions: int
    total_questions: int


class SWOTQuestionContext(BaseModel):
    axis_id: int
    axis_name: str
    question_id: int
    question_text: str

    score_code: Optional[str] = None
    score_value: Optional[int] = None
    score_label: Optional[str] = None
    score_description: Optional[str] = None

    max_score: Optional[int] = None
    answer_text: Optional[str] = None
    comment: Optional[str] = None

    theme: Optional[str] = None
    low_score_meaning: Optional[str] = None
    high_score_meaning: Optional[str] = None
    opportunity_hint: Optional[str] = None
    threat_hint: Optional[str] = None


class SWOTContextRead(BaseModel):
    company_id: int
    company_name: str
    status: str
    axis_scores: list[SWOTAxisScoreContext]
    questions: list[SWOTQuestionContext]

class SWOTCreate(BaseModel):
    axis_id: Optional[int] = None

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    opportunities: Optional[str] = None
    threats: Optional[str] = None

    generation_source: str = "manual"
    generated_by_ai: bool = False
    ai_model: Optional[str] = None
    status: str = "draft"


class SWOTRead(BaseModel):
    id: int
    company_id: int
    axis_id: Optional[int] = None

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    opportunities: Optional[str] = None
    threats: Optional[str] = None

    generation_source: str
    generated_by_ai: bool
    ai_model: Optional[str] = None
    status: str

    created_by_user_id: Optional[int] = None
    validated_by_user_id: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


