import random
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User
from app.tasks.email_tasks import send_password_reset_email, send_verification_email

router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyRequest(BaseModel):
    email: str
    code: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")


    code = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=15)


    hashed = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=expires,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    send_verification_email.delay(new_user.email, code)

    return {
        "message": "Konto utworzone. Sprawdź e-mail i potwierdź rejestrację kodem.",
        "email": new_user.email
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Konto niezweryfikowane. Sprawdź email.")

    token = create_access_token({"sub": user.email})
    return {"access_token": token}

@router.post("/verify")
async def verify_account(
        data: VerifyRequest,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid request")

    if user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid code")

    if user.verification_code_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Code expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    await db.commit()

    return {"message": "Konto zweryfikowane. Możesz się zalogować."}


@router.post("/forgot_pasword")
async def forgot_password(
        data: ForgotPasswordRequest,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user:
        token = secrets.token_urlsafe(32)
        user.reset_password_token = token
        user.reset_password_expires_at = datetime.now(UTC) + timedelta(hours=1)
        await db.commit()

        reset_link = f"http://localhost:8000/reset-password?token={token}"
        send_password_reset_email.delay(user.email, reset_link)

    return {
        "message": "Jeśli email istnieje w bazie, wysłaliśmy link do resetu hasła."
    }

@router.post("/reset_password")
async def reset_password(
        data: ResetPasswordRequest,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.reset_password_token == data.token))
    user = result.scalar_one_or_none()

    if not user or user.reset_password_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Nieprawidłowy lub wygasły token.")

    user.hashed_password = get_password_hash(data.new_password)
    user.reset_password_token = None
    user.reset_password_expires_at = None
    await db.commit()

    return {"message": "Hasło zostało zmienione, Możesz się zalogować."}
