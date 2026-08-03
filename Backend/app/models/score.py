from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)

    score_total = Column(Integer, nullable=False, default=0)
    score_max = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0)

    answered_questions = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())