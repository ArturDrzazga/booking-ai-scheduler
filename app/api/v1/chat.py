from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models import Booking, BookingStatus, Service, Staff, User
from app.services.ai_chat import AIBookingChat

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    staff_id: int
    service_id: int
    date: str


@router.post("/")
async def chat(
        data: ChatMessage,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Chat with Ai endpoint"""
    result = await db.execute(
        select(Service).where(Service.id == data.service_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    result = await db.execute(
        select(Staff).where(Staff.id == data.staff_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    chat_service = AIBookingChat(db, current_user.id)
    date = datetime.fromisoformat(data.date)

    context = await chat_service.get_schedule_context(
        staff_id=data.staff_id,
        date=date,
        duration_time=service.duration_time,
    )

    response = await chat_service.chat(data.message, context)

    if response.get("ready_to_book") and response.get("bookings_details"):
        details = response["bookings_details"]
        start_time = datetime.fromisoformat(details["start_time"])
        end_time = start_time + timedelta(minutes=service.duration_time)

        booking = Booking(
            user_id=current_user.id,
            service_id=service.id,
            staff_id=staff.id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            total_price=service.price,
            deposit_amount=0.0,
            deposit_paid=False,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        response["booking_id"] = booking.id

    return response