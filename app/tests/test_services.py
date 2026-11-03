import pytest


@pytest.mark.asyncio
async def test_create_service(client, admin_token):
    """Tests creating a new service as admin."""
    response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Manicure",
            "description": "Klasyczny manicure",
            "duration_time": 60,
            "price": 120.0
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Manicure"
    assert data["price"] == 120.0


@pytest.mark.asyncio
async def test_create_service_unauthorized(client, user_token):
    """Tests that a regular user cannot create a service."""
    response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Manicure",
            "duration_time": 60,
            "price": 120.0
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_services(client, test_service):
    """Tests listing all services."""
    response = await client.get("/api/v1/services/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_service.name


@pytest.mark.asyncio
async def test_get_service(client, test_service):
    """Tests retrieving a single service by ID."""
    response = await client.get(f"/api/v1/services/{test_service.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_service.id


@pytest.mark.asyncio
async def test_update_service(client, admin_token, test_service):
    """Tests updating a service."""
    response = await client.put(
        f"/api/v1/services/{test_service.id}",
        json={"price": 150.0},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["price"] == 150.0


@pytest.mark.asyncio
async def test_delete_service(client, admin_token, test_service):
    """Tests deleting a service."""
    response = await client.delete(
        f"/api/v1/services/{test_service.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_service_not_found(client, admin_token):
    """Tests deleting a non-existent service."""
    response = await client.delete(
        "/api/v1/services/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404