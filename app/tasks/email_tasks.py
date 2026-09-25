import asyncio

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import Booking, Salon, Service, Staff, User
from app.services.email_service import get_email_service


async def _get_session():
    """Create new engine and session for celery task"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session(), engine


@shared_task
def send_booking_confirmation(booking_id: int) -> None:
    """Send confirmation email to user"""
    asyncio.run(_send_confirmation(booking_id))


async def _send_confirmation(booking_id: int) -> None:
    session, engine = await _get_session()
    try:
        async with session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            if not booking:
                return

            user = await session.get(User, booking.user_id)
            service = await session.get(Service, booking.service_id)
            staff = await session.get(Staff, booking.staff_id)
            salon = await session.get(Salon, booking.salon_id)

            email = get_email_service()
            await email.send_email(
                to=user.email,
                subject="✅ Rezerwacja potwierdzona",
                template_name="booking_confirmation.html",
                context={
                    "customer_name": user.full_name or user.email,
                    "service_name": service.name,
                    "staff_name": staff.name,
                    "start_time": booking.start_time.strftime("%d.%m.%Y %H:%M"),
                    "duration": service.duration_time,
                    "total_price": booking.total_price,
                    "deposit_amount": booking.deposit_amount,
                    "deposit_status": "opłacona" if booking.deposit_paid else "do zapłaty",
                    "salon_name": salon.name,
                    "salon_address": "",
                },
            )
    finally:
        await engine.dispose()


@shared_task
def send_booking_reminder(booking_id: int) -> None:
    """Send reminder email to user"""

    async def _send_reminder(booking_id: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalar_one_or_none()
            if not booking:
                return

            user = await db.get(User, booking.user_id)
            service = await db.get(Service, booking.service_id)
            staff = await db.get(Staff, booking.staff_id)
            salon = await db.get(Salon, booking.salon_id)

            email = get_email_service()
            await email.send_email(
                to=user.email,
                subject="🔔 Przypomnienie o jutrzejszej wizycie",
                template_name="booking_reminder.html",
                context={
                    "customer_name": user.fullname or user.email,
                    "service_name": service.name,
                    "staff_name": staff.name,
                    "start_time": booking.start_time.strftime("%d.%m.%Y %H:%M"),
                    "salon_name": salon.name,
                },
            )