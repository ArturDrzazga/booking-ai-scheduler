from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)

    total_price = Column(Integer, nullable=False)
    deposit_amount = Column(Float, nullable=False)
    deposit_paid = Column(Boolean, nullable=False)

    payment_intent_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="bookings")
    service = relationship("Service", backref="bookings")
    staff = relationship("Staff", backref="bookings")

    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False)
    salon = relationship("Salon", backref="bookings")
