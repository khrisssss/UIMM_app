from pydantic import BaseModel
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = "Prospect"  # Default value for status

class CompanyCreate(CompanyBase):
    pass # when creating a company, use the same fields as CompanyBase

class CompanyRead(CompanyBase):
    id: int
    is_archived: bool = False  # Default value for is_archived

    class Config:
        from_attributes = True  # This allows Pydantic to read data from SQLAlchemy models