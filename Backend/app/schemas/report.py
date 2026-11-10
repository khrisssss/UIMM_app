from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    executive_summary: Optional[str] = None
    diagnostic_summary: Optional[str] = None
    axis_analysis: Optional[str] = None
    presentation_content: Optional[str] = None
    swot_summary: Optional[str] = None
    recommendations: Optional[str] = None
    conclusion: Optional[str] = None
    status: Optional[str] = None

class ReportRead(BaseModel):
    id: int
    company_id: int

    title: str
    executive_summary: Optional[str] = None
    diagnostic_summary: Optional[str] = None
    axis_analysis: Optional[str] = None
    presentation_content: Optional[str] = None
    swot_summary: Optional[str] = None
    recommendations: Optional[str] = None
    conclusion: Optional[str] = None

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