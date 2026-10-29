from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql.functions import func

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    phone_number = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_code = Column(String(6), nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), default=15)

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
