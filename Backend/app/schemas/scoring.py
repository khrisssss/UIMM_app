from pydantic import BaseModel
from typing import Optional


class ScoringLevelRead(BaseModel):
    id: int
    scoring_scale_id: int
    code: str
    score_value: Optional[int] = None
    label: str
    description: Optional[str] = None
    order_index: int

    class Config:
        from_attributes = True


class ScoringScaleRead(BaseModel):
    id: int
    axis_id: int
    name: str
    description: Optional[str] = None
    max_score: int
    is_active: bool

    levels: list[ScoringLevelRead]