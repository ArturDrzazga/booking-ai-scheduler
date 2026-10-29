from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)

    salon_name = Column(String(100), default="Mój Salon")
    address = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    instagram_url = Column(String(255), nullable=True)
    logo_url = Column(String(255), nullable=True)

    work_hours = Column(JSON, default={
        "monday": {"start": "09:00", "end": "17:00"},
        "tuesday": {"start": "09:00", "end": "17:00"},
        "wednesday": {"start": "09:00", "end": "17:00"},
        "thursday": {"start": "09:00", "end": "17:00"},
        "friday": {"start": "09:00", "end": "17:00"},
        "saturday": {"start": "10:00", "end": "14:00"},
        "sunday": None
    })
    buffer_minutes = Column(Integer, default=15)
    cancellation_hours = Column(Integer, default=24)

    deposit_enabled = Column(Boolean, default=False)
    deposit_percentage = Column(Integer, default=50)

    email_notifications = Column(Boolean, default=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    email_from_name = Column(String(100), default="Mój Salon")
    email_reply_to = Column(String(100), nullable=True)

    sms_notifications = Column(Boolean, default=False)
    twilio_account_sid = Column(String(100), nullable=True)
    twilio_auth_token = Column(String(100), nullable=True)
    twilio_phone_number = Column(String(20), nullable=True)

    ai_api_key = Column(String(255), nullable=True)

    terms_of_service = Column(Text, nullable=True)
    privacy_policy = Column(Text, nullable=True)
    cancellation_policy = Column(Text, nullable=True)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())