from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyAxisUpdate(BaseModel):
    is_selected: Optional[bool] = None
    #for_mission_complementaire: Optional[bool] = None
    diagnostic_comment: Optional[str] = None

class CompanyAxisRead(BaseModel):
    id: int
    company_id: int
    axis_id: int
    axis_name: str
    axis_description: Optional[str] = None
    axis_order_index: int
    is_selected: bool
   # for_mission_complementaire: bool
    created_at: datetime
    updated_at: datetime
    diagnostic_comment: Optional[str] = None
    class Config:
        from_attributes = True


class DiagnosticAxisOverview(BaseModel):
    axis_id: int
    axis_name: str
    axis_order_index: int
    is_selected: bool
   # for_mission_complementaire: bool
    answered_questions: int
    total_questions: int
    progress_percentage: int

class CompanyAxisUpdate(BaseModel):
    is_selected: Optional[bool] = None
   # for_mission_complementaire: Optional[bool] = None
    diagnostic_comment: Optional[str] = None