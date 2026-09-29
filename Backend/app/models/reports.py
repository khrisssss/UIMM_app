from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    title = Column(String, nullable=False)
    executive_summary = Column(Text, nullable=True)
    diagnostic_summary = Column(Text, nullable=True)
    axis_analysis = Column(Text, nullable=True)
    swot_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    generation_source = Column(String, nullable=False, default="manual")
    generated_by_ai = Column(Boolean, nullable=False, default=False)
    ai_model = Column(String, nullable=True)

    status = Column(String, nullable=False, default="draft")

    created_by_user_id = Column(Integer, nullable=True)
    validated_by_user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())