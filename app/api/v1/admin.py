import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_settings
from app.core.database import get_db
from app.core.encryption import encrypt_data
from app.models import Booking, BookingStatus, Service, Settings, Staff, User

router = APIRouter()


class SettingsUpdate(BaseModel):
    salon_name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    logo_url : str | None = None

    work_hours: dict | None = None
    buffer_minutes: int | None = None
    cancellation_hours: int | None = None

    deposit_enabled: bool | None = None
    deposit_percentage: int | None = None

    email_notifications: bool | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from_name: str | None = None
    email_reply_to: str | None = None

    sms_notifications: bool | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None

    ai_api_key: str | None = None

    terms_of_service: str | None = None
    privacy_policy: str | None = None
    cancellation_policy: str | None = None


class SettingsResponse(BaseModel):
    salon_name: str
    address: str | None
    phone: str | None
    email: str | None
    instagram_url: str | None
    logo_url: str | None
    work_hours: dict
    buffer_minutes: int
    cancellation_hours: int
    deposit_enabled: bool
    deposit_percentage: int
    email_notifications: bool
    email_from_name: str | None
    email_reply_to: str | None
    sms_notifications: bool
    terms_of_service: str | None
    privacy_policy: str | None
    cancellation_policy: str | None

    class Config:
        from_attributes = True


class BlockTimeCreate(BaseModel):
    staff_id: int
    start_time: datetime
    end_time: datetime
    reason: str | None = None


class AdminBookingCreate(BaseModel):
    client_id: int | None = None
    client_name: str | None = None
    client_phone: str | None = None
    client_email: str | None = None

    service_id: int
    staff_id: int
    start_time: datetime
    notes: str | None = None


@router.get("/settings", response_model=SettingsResponse)
async def get_admin_settings(
        settings: Settings = Depends(get_settings),
        admin: User = Depends(get_current_admin),
):
    """Downloads system settings (only admin)"""
    return settings

@router.patch("/settings", response_model=SettingsResponse)
async def update_admin_settings(
        data: SettingsUpdate,
        db: AsyncSession = Depends(get_db),
        settings: Settings = Depends(get_settings),
        admin: User = Depends(get_current_admin),
):
    """Updates system settings (only admin)"""

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key in ["smtp_password", "twilio_auth_token", "ai_api_key"]:
            continue

        if hasattr(settings, key):
            setattr(settings, key, value)

    if data.smtp_password:
        settings.smtp_password = encrypt_data(data.smtp_password)
    if data.twilio_auth_token:
        settings.twilio_auth_token = encrypt_data(data.twilio_auth_token)
    if data.ai_api_key:
        settings.ai_api_key = encrypt_data(data.ai_api_key)

    await db.commit()
    await db.refresh(settings)
    return settings


@router.post("/block-time")
async def block_time(
        data: BlockTimeCreate,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(get_current_admin),
):
    block = Booking(
        user_id=None,
        staff_id=data.staff_id,
        service_id=None,
        start_time=data.start_time,
        end_time=data.end_time,
        status=BookingStatus.CONFIRMED,
        total_price=0,
        deposit_amount=0,
        deposit_paid=False,
        notes=data.reason or "Rezerwacja czasu",
        is_blocker=True
    )

    db.add(block)
    await db.commit()
    return {"message": "Czas zarezerwowany"}

@router.get("/clients/search")
async def search_client(
        query: str,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(get_current_admin),
):
    """Search clients by name, surname or phone number"""
    result = await db.execute(
        select(User).where(
            or_(
                User.full_name.ilike(f"%{query}%"),
                User.phone_number.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
            )
        ).limit(10)
    )
    clients = result.scalars().all()
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "phone_number": c.phone_number,
            "email": c.email,
            "is_guest": c.is_guest,
        }
        for c in clients
    ]


@router.post("/bookings")
async def create_admin_booking(
        data: AdminBookingCreate,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(get_current_admin),
):
    """Creates booking for phone clients or existing."""

    client = None
    if data.client_id:
        client = await db.get(User, data.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    elif data.client_phone:
        result = await db.execute(
            select(User).where(User.phone_number == data.client_phone)
        )
        client = result.scalar_one_or_none()

        if not client:
            client = User(
                email=data.client_email or f"guest_{data.client_phone}@temp.local",
                hashed_password="",
                full_name=data.client_name,
                phone_number=data.client_phone,
                is_guest=True,
                is_verified=False,
            )
            db.add(client)
            await db.flush()
    else:
        raise HTTPException(status_code=400, detail="Provide client_id or client_phone")

    service = await db.get(Service, data.service_id)
    staff = await db.get(Staff, data.staff_id)
    if not service or not staff:
        raise HTTPException(status_code=404, detail="Service or Staff not found")

    end_time = data.start_time + timedelta(minutes=service.duration_time)
    result = await db.execute(
        select(Booking).where(
            Booking.staff_id == staff.id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.DEPOSIT_PAID]),
            Booking.start_time < end_time,
            Booking.end_time > data.start_time,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Time slot already booked")

    booking = Booking(
        user_id=client.id,
        service_id=service.id,
        staff_id=staff.id,
        start_time=data.start_time,
        end_time=end_time,
        status=BookingStatus.CONFIRMED,
        total_price=service.price,
        deposit_amount=0,
        deposit_paid=False,
        notes=data.notes,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return {
        "id": booking.id,
        "client_name": client.full_name,
        "service": service.name,
        "start_time": booking.start_time,
    }


UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        admin: User = Depends(get_current_admin),
):
    """Upload image(logo, gallery)"""
    if file.content_type not in ["image/png", "image/web", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Dozwolone są tylko pliki JPG, PNG i WEBP.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Plik jest za duży (max 5 MB).")

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return {"url": f"/static/uploads/{filename}"}