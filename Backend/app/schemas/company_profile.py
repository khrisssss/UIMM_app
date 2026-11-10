from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CompanyProfileSectionBase(BaseModel):
    name: str
    order_index: Optional[int] = 1
    is_active: Optional[bool] = True


class CompanyProfileSectionCreate(CompanyProfileSectionBase):
    pass


class CompanyProfileSectionUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class CompanyProfileSectionRead(CompanyProfileSectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileQuestionBase(BaseModel):
    section_id: int
    question_text: str
    order_index: Optional[int] = 1
    is_active: Optional[bool] = True


class CompanyProfileQuestionCreate(CompanyProfileQuestionBase):
    pass


class CompanyProfileQuestionUpdate(BaseModel):
    section_id: Optional[int] = None
    question_text: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class CompanyProfileQuestionRead(BaseModel):
    id: int

    section_id: int
    section_name: str
    section_order_index: int

    question_text: str
    order_index: int
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileAnswerBase(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    comment: Optional[str] = None


class CompanyProfileAnswerCreate(CompanyProfileAnswerBase):
    pass


# Schéma inutilisé dans les routes actuelles, conservé pour référence.
# class CompanyProfileAnswerUpdate(BaseModel):
#     answer_text: Optional[str] = None
#     comment: Optional[str] = None


class CompanyProfileAnswerRead(CompanyProfileAnswerBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)