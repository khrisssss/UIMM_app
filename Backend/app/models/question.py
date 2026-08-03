from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)

    question_text = Column(String, nullable=False)
    question_type = Column(String, nullable=False, default="score")
    max_score = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    theme = Column(String, nullable=True)
    low_score_meaning = Column(String, nullable=True)
    high_score_meaning = Column(String, nullable=True)
    opportunity_hint = Column(String, nullable=True)
    threat_hint = Column(String, nullable=True)

    class Config:
        from_attributes = True  # This allows Pydantic to read data from SQLAlchemy models #Because now FastAPI will receive SQLAlchemy objects from PostgreSQL, not normal dictionaries.