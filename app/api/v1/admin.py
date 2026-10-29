from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_settings
from app.core.database import get_db
from app.core.encryption import encrypt_data
from app.models import Booking, BookingStatus, Settings, User

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
        notes=data.reason or "Rezerwacja czasu",
        is_blocker=True
    )

    db.add(block)
    await db.commit()
    return {"message": "Czas zarezerwowany"}