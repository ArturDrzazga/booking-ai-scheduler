# app/tests/test_auth.py

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
@patch("app.api.v1.auth.send_verification_email.delay")
async def test_register_success(mock_email, client):
    """Tests successful user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "nowy@test.pl",
        "password": "haslo123",
        "phone_number": "123456789",
        "full_name": "Nowy User"
    })
    assert response.status_code == 200
    assert "Konto utworzone" in response.json()["message"]
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_email(client, normal_user):
    """Tests registration with an existing email."""
    response = await client.post("/api/v1/auth/register", json={
        "email": normal_user.email,
        "password": "haslo123",
        "phone_number": "000000000",
        "full_name": "Ktoś Inny"
    })
    assert response.status_code == 400
    assert "już istnieje" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_phone(client):
    """Tests registration with an invalid phone number format."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "zly@test.pl",
        "password": "haslo123",
        "phone_number": "123",
        "full_name": "Zły User"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, normal_user):
    """Tests successful login."""
    response = await client.post("/api/v1/auth/login", json={
        "email": normal_user.email,
        "password": "haslo123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client, normal_user):
    """Tests login with an incorrect password."""
    response = await client.post("/api/v1/auth/login", json={
        "email": normal_user.email,
        "password": "zlehaslo"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unverified_user(client, db_session):
    """Tests login with an unverified account."""
    now = datetime.now(UTC)
    user = User(
        email="niezweryfikowany@test.pl",
        hashed_password=get_password_hash("haslo123"),  # ← prawdziwy hash
        phone_number="111111111",
        full_name="Niezweryfikowany",
        is_verified=False,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "haslo123"
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_account(client, db_session):
    """Tests successful account verification."""
    now = datetime.now(UTC)
    user = User(
        email="doweryfikacji@test.pl",
        hashed_password=get_password_hash("haslo123"),  # ← prawdziwy hash
        phone_number="222222222",
        full_name="Do Weryfikacji",
        is_verified=False,
        verification_code="123456",
        verification_code_expires_at=now + timedelta(minutes=10),
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/verify", json={
        "email": user.email,
        "code": "123456"
    })
    assert response.status_code == 200

    await db_session.refresh(user)
    assert user.is_verified is True
    assert user.verification_code is None


@pytest.mark.asyncio
async def test_verify_wrong_code(client, db_session):
    """Tests account verification with an incorrect code."""
    now = datetime.now(UTC)
    user = User(
        email="zlykod@test.pl",
        hashed_password=get_password_hash("haslo123"),  # ← prawdziwy hash
        phone_number="333333333",
        full_name="Zły Kod",
        is_verified=False,
        verification_code="123456",
        verification_code_expires_at=now + timedelta(minutes=10),
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/verify", json={
        "email": user.email,
        "code": "999999"
    })
    assert response.status_code == 400
    assert "Invalid code" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.api.v1.auth.send_password_reset_email.delay")
async def test_forgot_password(mock_email, client, normal_user):
    """Tests the forgot password request."""
    response = await client.post("/api/v1/auth/forgot-password", json={
        "email": normal_user.email
    })
    assert response.status_code == 200
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password(client, db_session):
    """Tests successful password reset."""
    now = datetime.now(UTC)
    user = User(
        email="reset@test.pl",
        hashed_password=get_password_hash("haslo123"),  # ← prawdziwy hash
        phone_number="444444444",
        full_name="Reset User",
        is_verified=True,
        reset_password_token="token123",
        reset_password_expires_at=now + timedelta(minutes=10),
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/reset-password", json={
        "token": "token123",
        "new_password": "nowehaslo"
    })
    assert response.status_code == 200
    assert "zmienione" in response.json()["message"]