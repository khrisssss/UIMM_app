from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class ScoringLevel(Base):
    __tablename__ = "scoring_levels"

    id = Column(Integer, primary_key=True, index=True)

    scoring_scale_id = Column(Integer, ForeignKey("scoring_scales.id"), nullable=False)

    code = Column(String, nullable=False)
    score_value = Column(Integer, nullable=True)

    label = Column(String, nullable=False)
    description = Column(String, nullable=True)

    order_index = Column(Integer, nullable=False)