from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class AxisQuestionCategory(Base):
    __tablename__ = "axis_question_categories"

    id = Column(Integer, primary_key=True, index=True)

    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)
    parent_category_id = Column (
        Integer,
        ForeignKey("axis_question_categories.id"),
        nullable=True,
    )

    name= Column(String, nullable=False)
    order_index = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    axis = relationship("Axis")
    parent_category = relationship("AxisQuestionCategory", remote_side=[id])