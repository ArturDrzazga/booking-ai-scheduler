from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_search_clients_admin(client, admin_token, normal_user):
    """Tests searching for clients as an admin."""
    response = await client.get(
        "/api/v1/admin/clients/search?query=Klient",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["email"] == normal_user.email


@pytest.mark.asyncio
async def test_search_clients_unauthorized(client, user_token):
    """Tests that a regular user cannot search clients."""
    response = await client.get(
        "/api/v1/admin/clients/search?query=Klient",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_admin_booking_with_new_client(
        client, admin_token, test_service, test_staff
):
    """Tests creating a booking for a new phone client."""
    start = (datetime.now(UTC) + timedelta(days=1)).replace(hour=10, minute=0)

    response = await client.post(
        "/api/v1/admin/bookings",
        json={
            "client_name": "Nowy Klient",
            "client_phone": "555666777",
            "service_id": test_service.id,
            "staff_id": test_staff.id,
            "start_time": start.isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == "Nowy Klient"
    assert data["service"] == test_service.name


@pytest.mark.asyncio
async def test_create_admin_booking_with_existing_client(
        client, admin_token, normal_user, test_service, test_staff
):
    """Tests creating a booking for an existing client by ID."""
    start = (datetime.now(UTC) + timedelta(days=2)).replace(hour=11, minute=0)

    response = await client.post(
        "/api/v1/admin/bookings",
        json={
            "client_id": normal_user.id,
            "service_id": test_service.id,
            "staff_id": test_staff.id,
            "start_time": start.isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == normal_user.full_name


@pytest.mark.asyncio
async def test_get_admin_settings(client, admin_token, test_settings):
    """Tests retrieving admin settings."""
    response = await client.get(
        "/api/v1/admin/settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["salon_name"] == "Test Salon"


@pytest.mark.asyncio
async def test_update_admin_settings(client, admin_token, test_settings):
    """Tests updating admin settings."""
    response = await client.patch(
        "/api/v1/admin/settings",
        json={"salon_name": "Nowa Nazwa"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["salon_name"] == "Nowa Nazwa"


@pytest.mark.asyncio
async def test_block_time(client, admin_token, test_staff):
    """Tests creating a time block."""
    start = (datetime.now(UTC) + timedelta(days=5)).replace(hour=12, minute=0)
    end = start + timedelta(hours=2)

    response = await client.post(
        "/api/v1/admin/block-time",
        json={
            "staff_id": test_staff.id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "reason": "Przerwa"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "Czas zarezerwowany" in response.json()["message"]