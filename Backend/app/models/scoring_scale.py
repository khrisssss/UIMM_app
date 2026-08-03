from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base


class ScoringScale(Base):
    __tablename__ = "scoring_scales"

    id = Column(Integer, primary_key=True, index=True)

    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    max_score = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)