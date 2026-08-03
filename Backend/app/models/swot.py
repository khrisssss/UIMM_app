from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database import Base


class SWOT(Base):
    __tablename__ = "swots"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=True)

    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    opportunities = Column(Text, nullable=True)
    threats = Column(Text, nullable=True)

    generation_source = Column(String, nullable=False, default="manual")
    generated_by_ai = Column(Boolean, nullable=False, default=False)
    ai_model = Column(String, nullable=True)

    status = Column(String, nullable=False, default="draft")

    created_by_user_id = Column(Integer, nullable=True)
    validated_by_user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())