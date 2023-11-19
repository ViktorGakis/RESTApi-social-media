import pytest
from fastapi import Request, status
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


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.net", "1234")
    confirmation_url = f"{spy.spy_return}"
    response = await async_client.get(confirmation_url)

    assert response.status_code == status.HTTP_200_OK
    assert "User confirmed" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response: Request = await async_client.get("/confirm/invalid_token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("RESTApi.security.confirm_token_expire_minutes", return_value=-1)
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.net", "1234")
    confirmation_url = f"{spy.spy_return}"
    response = await async_client.get(confirmation_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response: Response = await async_client.post(
        "/token", json={"email": "test@example.net", "password": "1234"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user_not_confirmed(
    async_client: AsyncClient, registered_user: dict
):
    response: Response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response: Response = await async_client.post(
        "/token",
        json={
            "email": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
