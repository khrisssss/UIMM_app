from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date
from sqlalchemy.sql import func

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)

    address = Column(String, nullable=True)
    company_size = Column(String, nullable=True)

    status = Column(String, nullable=False, default="Prospect")
    is_archived = Column(Boolean, nullable=False, default=False)

    prediag_origin = Column(String, nullable=True)
    prediag_origin_other = Column(String, nullable=True)

    has_rse = Column(Boolean, nullable=False, default=False)
    specific_regulatory_constraints = Column(Text, nullable=True)

    general_comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    diagnostic_referent = Column(String, nullable=True)
    diagnostic_launch_date = Column(Date, nullable=True)
    diagnostic_restitution_date = Column(Date, nullable=True)

    mission_consultant = Column(String, nullable=True)
    mission_launch_date = Column(Date, nullable=True)
    mission_restitution_date = Column(Date, nullable=True)
    diagnostic_referent = Column(String, nullable=True)
    diagnostic_launch_date = Column(Date, nullable=True)
    diagnostic_restitution_date = Column(Date, nullable=True)

    mission_consultant = Column(String, nullable=True)
    mission_launch_date = Column(Date, nullable=True)
    mission_restitution_date = Column(Date, nullable=True)

    general_state = Column(String, nullable=False, default="orange")
