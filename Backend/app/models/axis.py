from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Axis(Base):
    __tablename__ = "axes"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    order_index = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)