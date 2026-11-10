from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyAxisUpdate(BaseModel):
    is_selected: Optional[bool] = None
    diagnostic_comment: Optional[str] = None
    show_in_portfolio: Optional[bool] = None

class CompanyAxisRead(BaseModel):
    id: int
    company_id: int
    axis_id: int
    axis_name: str
    axis_description: Optional[str] = None
    axis_order_index: int
    is_selected: bool
    created_at: datetime
    updated_at: datetime
    diagnostic_comment: Optional[str] = None
    show_in_portfolio: bool
    class Config:
        from_attributes = True


class DiagnosticAxisOverview(BaseModel):
    axis_id: int
    axis_name: str
    axis_order_index: int
    is_selected: bool
    answered_questions: int
    total_questions: int
    progress_percentage: int
