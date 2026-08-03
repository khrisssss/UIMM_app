from pydantic import BaseModel
from typing import Optional


class AxisRead(BaseModel):
    id:int #axis ID
    name: str #Stratégie, Performance, etc.
    description: Optional[str] = None  #optional explanation
    order_index: int #display order
    is_active: bool = True  # Default value for is_active #active or hidden

    class Config:
        from_attributes = True  # This allows Pydantic to read data from SQLAlchemy models #Because now FastAPI will receive SQLAlchemy objects from PostgreSQL, not normal dictionaries.