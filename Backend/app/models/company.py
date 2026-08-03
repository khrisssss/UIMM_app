from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    size = Column(String, nullable=True)

    status = Column(String, nullable=False, default="Prospect")

    is_archived = Column(Boolean, nullable=False, default=False)