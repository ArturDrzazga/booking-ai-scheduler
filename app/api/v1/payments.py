from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_salon, get_current_user
from app.core.database import get_db
from app.models import Booking, Salon
from app.services.payment_service import get_payment_service

router = APIRouter()


@router.post("/bookings/{booking_id}/pay")
async def create_payment(
    booking_id: int,
    salon: Salon = Depends(get_current_salon),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create deposit paid for booking"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.salon_id == salon.id,
            Booking.user_id == current_user.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.deposit_paid:
        raise HTTPException(status_code=400, detail="Payment already paid")

    if booking.deposit_amount <= 0:
        raise HTTPException(status_code=400, detail="No deposit required")

    service = get_payment_service()
    payment_data = await service.create_deposit_payment(booking)
    return payment_data


@router.post("/bookings/{booking_id}/mock-confirm")
async def mock_confirm_payment(
    booking_id: int,
    salon: Salon = Depends(get_current_salon),
    db: AsyncSession = Depends(get_db),
):
    """Simulates payment confirmation(mock)"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.salon_id == salon.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    service = get_payment_service()
    payment_id = f"mock_{booking.id}"

    try:
        updated = await service.confirm_payment(booking, payment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "status": "success",
        "message": "Payment confirmed (mock)",
        "booking_id": booking.id,
        "booking_status": updated.status.value,
    }
