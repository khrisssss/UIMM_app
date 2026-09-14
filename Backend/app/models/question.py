from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)

    question_text = Column(Text, nullable=False)
    theme = Column(String, nullable=True)

    order_index = Column(Integer, nullable=False, default=1)
    max_score = Column(Integer, nullable=True, default=5)
    is_active = Column(Boolean, nullable=False, default=True)

    target_less_than_10 = Column(Boolean, nullable=False, default=True)
    target_11_to_50 = Column(Boolean, nullable=False, default=True)
    target_more_than_50 = Column(Boolean, nullable=False, default=True)

    category_id = Column(Integer, ForeignKey("axis_question_categories.id"), nullable=True,)
    category = relationship("AxisQuestionCategory")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    axis = relationship("Axis")