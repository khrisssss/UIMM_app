from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CompanyAxis(Base):
    __tablename__ = "company_axes"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    axis_id = Column(Integer, ForeignKey("axes.id"), nullable=False)

    is_selected = Column(Boolean, nullable=False, default=True)
    for_mission_complementaire = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    axis = relationship("Axis")
    diagnostic_comment = Column(Text, nullable=True)