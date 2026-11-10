from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, date

from app.services.siren import normalize_siren


class CompanyBase(BaseModel):
    name: str
    siren: Optional[str] = None
    status: Optional[str] = "Prospect"

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    address: Optional[str] = None
    company_size: Optional[str] = None

    prediag_origin: Optional[str] = None
    prediag_origin_other: Optional[str] = None

    has_rse: Optional[bool] = False
    specific_regulatory_constraints: Optional[str] = None

    general_comment: Optional[str] = None

    diagnostic_referent: Optional[str] = None
    diagnostic_launch_date: Optional[date] = None
    diagnostic_restitution_date: Optional[date] = None

    mission_consultant: Optional[str] = None
    mission_launch_date: Optional[date] = None
    mission_restitution_date: Optional[date] = None
    general_state: Optional[str] = "orange"

    @field_validator("siren", mode="before")
    @classmethod
    def check_siren(cls, value):
        return normalize_siren(value)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    siren: Optional[str] = None
    status: Optional[str] = None

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    address: Optional[str] = None
    company_size: Optional[str] = None

    status: Optional[str] = None
    is_archived: Optional[bool] = None
    
    prediag_origin: Optional[str] = None
    prediag_origin_other: Optional[str] = None

    has_rse: Optional[bool] = None
    specific_regulatory_constraints: Optional[str] = None

    general_comment: Optional[str] = None
    diagnostic_referent: Optional[str] = None
    diagnostic_launch_date: Optional[date] = None
    diagnostic_restitution_date: Optional[date] = None

    mission_consultant: Optional[str] = None
    mission_launch_date: Optional[date] = None
    mission_restitution_date: Optional[date] = None

    general_state: Optional[str] = None

    @field_validator("siren", mode="before")
    @classmethod
    def check_siren(cls, value):
        return normalize_siren(value)


class CompanyRead(CompanyBase):
    is_synthetic: bool = False
    id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)