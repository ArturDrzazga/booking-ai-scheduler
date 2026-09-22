from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False)
    salon = relationship("Salon", backref="staff")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
