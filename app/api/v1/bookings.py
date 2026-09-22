from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_salon, get_current_user
from app.core.database import get_db
from app.models import Booking, BookingStatus, Salon, Service, Staff

router = APIRouter()

class BookingCreate(BaseModel):
    service_id: int
    staff_id: int
    start_time: datetime
    notes: str | None = None


class BookingResponse(BaseModel):
    id: int
    user_id: int
    service_id: int
    staff_id: int
    start_time: datetime
    end_time: datetime
    status: str
    total_price: float
    deposit_amount: float
    deposit_paid: bool
    notes: str | None

    class Config:
        from_attributes = True


class BookingUpdate(BaseModel):
    service_id: int | None = None
    staff_id: int | None = None
    start_time: datetime | None = None
    notes: str | None = None
    status: str | None = None


@router.get("/", response_model=list[BookingResponse])
async def list_bookings(
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Booking).where(Booking.salon_id == salon.id)
    )
    return result.scalars().all()

@router.post("/", response_model=BookingResponse)
async def create_booking(
        data: BookingCreate,
        salon: Salon = Depends(get_current_salon),
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == data.service_id,
            Service.salon_id == salon.id,
        )
    )

    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    result = await db.execute(
        select(Staff).where(
            Staff.id == data.staff_id,
            Staff.salon_id == salon.id,
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    end_time = data.start_time + timedelta(minutes=service.duration_time)

    result = await db.execute(
        select(Booking).where(
            Booking.salon_id == salon.id,
            Booking.staff_id == staff.id,
            Booking.status.in_(
                [
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.DEPOSIT_PAID,
                ]
            ),
            Booking.start_time < end_time,
            Booking.end_time > data.start_time,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Time slot already exists")

    deposit_amount = 0.0
    if salon.deposit_enabled:
        deposit_amount = service.price * (salon.deposit_percentage / 100)

    booking = Booking(
        salon_id=salon.id,
        user_id=current_user.id,
        service_id=service.id,
        staff_id=staff.id,
        start_time=data.start_time,
        end_time=end_time,
        status=BookingStatus.PENDING,
        total_price=service.price,
        deposit_amount=deposit_amount,
        deposit_paid=False,
        notes=data.notes,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
        booking_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.salon_id == salon.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
        booking_id: int,
        data: BookingUpdate,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.salon_id == salon.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if data.service_id is not None:
        result = await db.execute(
            select(Service).where(
                Service.id == data.service_id,
                Service.salon_id == salon.id
            )
        )
        service = result.scalar_one_or_none()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        booking.service_id = service.id
        booking.total_price = service.price

    if data.staff_id is not None:
        result = await db.execute(
            select(Staff).where(
                Staff.id == data.staff_id,
                Staff.salon_id == salon.id
            )
        )
        staff = result.scalar_one_or_none()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        booking.staff_id = staff.id

    if data.start_time is not None:
        result = await db.execute(
            select(Service).where(Service.id == booking.service_id)
        )
        service = result.scalar_one_or_none()
        end_time = data.start_time + timedelta(minutes=service.duration_time)

        result = await db.execute(
            select(Booking).where(
                Booking.salon_id == salon.id,
                Booking.staff_id == booking.staff_id,
                Booking.id != booking.id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.DEPOSIT_PAID]),
                Booking.start_time < end_time,
                Booking.end_time > data.start_time
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Time slot already booked")

        booking.start_time = data.start_time
        booking.end_time = end_time

    if data.notes is not None:
        booking.notes = data.notes

    if data.status is not None:
        booking.status = data.status

    await db.commit()
    await db.refresh(booking)
    return booking

@router.delete("/{booking_id}")
async def delete_booking(
        booking_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.salon_id == salon.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = BookingStatus.CANCELED
    await db.commit()
    return {"message": "Booking canceled"}