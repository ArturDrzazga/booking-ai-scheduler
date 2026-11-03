from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.models.booking import Booking, BookingStatus


@pytest.mark.asyncio
@patch("app.api.v1.bookings.send_booking_confirmation.delay")
async def test_create_booking_success(
        mock_email, client, user_token, test_service, test_staff
):
    """Tests successful booking creation."""
    start = (datetime.now(UTC) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": test_service.id,
            "staff_id": test_staff.id,
            "start_time": start.isoformat()
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_create_booking_unauthorized(client, test_service, test_staff):
    """Tests booking creation without authentication."""
    start = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    response = await client.post(
        "/api/v1/bookings/",
        json={"service_id": test_service.id, "staff_id": test_staff.id, "start_time": start}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_booking_collision(
        client, db_session, user_token, test_service, test_staff
):
    """Tests collision detection for overlapping bookings."""
    start = (datetime.now(UTC) + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=test_service.duration_time)

    booking = Booking(
        user_id=1,
        service_id=test_service.id,
        staff_id=test_staff.id,
        start_time=start,
        end_time=end,
        status=BookingStatus.CONFIRMED,
        total_price=100,
        deposit_amount=0,
        deposit_paid=False
    )
    db_session.add(booking)
    await db_session.commit()

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": test_service.id,
            "staff_id": test_staff.id,
            "start_time": start.isoformat()
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancel_booking(client, db_session, user_token, test_service, test_staff, normal_user):
    """Tests booking cancellation."""
    start = (datetime.now(UTC) + timedelta(days=3)).replace(hour=14, minute=0)
    end = start + timedelta(minutes=test_service.duration_time)

    booking = Booking(
        user_id=normal_user.id,
        service_id=test_service.id,
        staff_id=test_staff.id,
        start_time=start,
        end_time=end,
        status=BookingStatus.PENDING,
        total_price=100,
        deposit_amount=0,
        deposit_paid=False
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.delete(
        f"/api/v1/bookings/{booking.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200

    await db_session.refresh(booking)
    assert booking.status == BookingStatus.CANCELED


@pytest.mark.asyncio
async def test_booking_on_blocked_time(
        client, db_session, user_token, test_service, test_staff
):
    """Tests that bookings cannot be made during blocked time."""
    start = (datetime.now(UTC) + timedelta(days=4)).replace(hour=9, minute=0)
    end = start + timedelta(hours=2)

    block = Booking(
        user_id=None,
        service_id=None,
        staff_id=test_staff.id,
        start_time=start,
        end_time=end,
        status=BookingStatus.CONFIRMED,
        total_price=0,
        deposit_amount=0,
        deposit_paid=False,
        is_blocker=True
    )
    db_session.add(block)
    await db_session.commit()

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": test_service.id,
            "staff_id": test_staff.id,
            "start_time": (start + timedelta(minutes=30)).isoformat()
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400