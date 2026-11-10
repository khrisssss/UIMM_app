from pydantic import BaseModel, ConfigDict
from typing import Optional


class AxisBase(BaseModel):
    name: str
    description: Optional[str] = None
    order_index: int
    is_active: bool = True


class AxisUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class AxisRead(AxisBase):
    id: int

    model_config = ConfigDict(from_attributes=True)