from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyPublicDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    siren: str
    legal_name: Optional[str] = None
    legal_form_code: Optional[str] = None
    naf_code: Optional[str] = None
    naf_section: Optional[str] = None
    headcount_code: Optional[str] = None
    headcount_label: Optional[str] = None
    company_category: Optional[str] = None
    creation_date: Optional[date] = None
    is_active: Optional[bool] = None
    head_office_address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    website_description: Optional[str] = None
    sector_active_companies: Optional[int] = None
    sources: str
    collected_at: datetime
