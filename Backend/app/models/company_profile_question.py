from sqlalchemy import Column, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CompanyProfileQuestion(Base):
    __tablename__ = "company_profile_questions"

    id = Column(Integer, primary_key=True, index=True)

    section_id = Column(
        Integer,
        ForeignKey("company_profile_sections.id"),
        nullable=False,
    )

    question_text = Column(Text, nullable=False)

    order_index = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    section = relationship("CompanyProfileSection")