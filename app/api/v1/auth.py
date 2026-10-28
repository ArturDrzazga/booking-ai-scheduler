import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User
from app.tasks.email_tasks import send_verification_email

router = APIRouter()


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    phone_number: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyRequest(BaseModel):
    email: str
    code: str


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
        fullname=user_data.full_name,
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

    if user.verification_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    await db.commit()

    return {"message": "Konto zweryfikowane. Możesz się zalogować."}