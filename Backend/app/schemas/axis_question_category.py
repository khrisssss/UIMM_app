from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AxisQuestionCategoryBase(BaseModel):
    axis_id: int
    parent_category_id: Optional[int] = None
    name: str
    order_index: Optional[int] = 1
    is_active: Optional[bool] = True


class AxisQuestionCategoryCreate(AxisQuestionCategoryBase):
    pass


class AxisQuestionCategoryUpdate(BaseModel):
    axis_id: Optional[int] = None
    parent_category_id: Optional[int] = None
    name: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class AxisQuestionCategoryRead(BaseModel):
    id: int
    axis_id: int
    axis_name: str
    parent_category_id: Optional[int] = None
    parent_category_name: Optional[str] = None
    name: str
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True