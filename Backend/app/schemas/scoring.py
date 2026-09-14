from pydantic import BaseModel
from typing import Optional


class ScoringLevelRead(BaseModel):
    id: int
    scoring_scale_id: int
    code: str
    label: str
    score_value: Optional[float] = None
    description: Optional[str] = None
    order_index: int

    class Config:
        from_attributes = True


class ScoringScaleRead(BaseModel):
    id: int
    axis_id: int
    name: str
    description: Optional[str] = None
    max_score: float
    is_active: bool
    levels: list[ScoringLevelRead] = []

    class Config:
        from_attributes = True


class ScoringScaleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[float] = None
    is_active: Optional[bool] = None
