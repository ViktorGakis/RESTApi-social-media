import pytest
from fastapi import status
from httpx import AsyncClient, Response


async def register_user(
    async_client: AsyncClient, email: str, password: str
) -> Response:
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response: Response = await register_user(async_client, "test@example.net", "1234")
    assert response.status_code == status.HTTP_201_CREATED
    assert "User created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    response = await register_user(
        async_client, registered_user["email"], registered_user["password"]
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "already exists" in response.json()["detail"]
