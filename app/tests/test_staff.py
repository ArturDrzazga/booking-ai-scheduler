import pytest


@pytest.mark.asyncio
async def test_create_staff(client, admin_token):
    """Tests creating a new staff member as admin."""
    response = await client.post(
        "/api/v1/staff/",
        json={
            "name": "Maria Nowak",
            "bio": "Kosmetyczka",
            "photo_url": "https://example.com/maria.jpg"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Maria Nowak"
    assert data["bio"] == "Kosmetyczka"


@pytest.mark.asyncio
async def test_create_staff_unauthorized(client, user_token):
    """Tests that a regular user cannot create a staff member."""
    response = await client.post(
        "/api/v1/staff/",
        json={"name": "Maria Nowak"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_staff(client, test_staff):
    """Tests listing all staff members."""
    response = await client.get("/api/v1/staff/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_staff.name


@pytest.mark.asyncio
async def test_get_staff(client, test_staff):
    """Tests retrieving a single staff member by ID."""
    response = await client.get(f"/api/v1/staff/{test_staff.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_staff.id


@pytest.mark.asyncio
async def test_update_staff(client, admin_token, test_staff):
    """Tests updating a staff member."""
    response = await client.put(
        f"/api/v1/staff/{test_staff.id}",
        json={"bio": "Starsza fryzjerka"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Starsza fryzjerka"


@pytest.mark.asyncio
async def test_delete_staff(client, admin_token, test_staff):
    """Tests deleting a staff member."""
    response = await client.delete(
        f"/api/v1/staff/{test_staff.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_staff_not_found(client, admin_token):
    """Tests deleting a non-existent staff member."""
    response = await client.delete(
        "/api/v1/staff/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404