from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CompanyProfileAnswer(Base):
    __tablename__ = "company_profile_answers"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_id = Column(
        Integer,
        ForeignKey("company_profile_questions.id"),
        nullable=False,
    )

    answer_text = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    question = relationship("CompanyProfileQuestion")