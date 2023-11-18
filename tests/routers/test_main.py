import pytest
from fastapi import status
from httpx import AsyncClient, Response
from starlette.status import HTTP_201_CREATED

from RESTApi.security import create_access_token


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response: Response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response: Response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response: Response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test Post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test Comment", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, registered_user: dict, logged_in_token: str
):
    body = "Test Post"
    response: Response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "user_id": registered_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    mocker.patch("RESTApi.security.access_token_expire_minutes", return_value=-1)
    token = create_access_token(registered_user["email"])
    print(f"{token=}")
    response: Response = await async_client.post(
        "/post",
        json={"body": "test post"},
        headers={"authorization": f"bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    response: Response = await async_client.post(
        "/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response: Response = await async_client.get("/post")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_post]


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    body: str = "Test Comment"
    response: Response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": registered_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
) -> None:
    response: Response = await async_client.get(f"/post/{created_post['id']}/comment")

    # pytest has a way of parametrizing
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response: Response = await async_client.get(f"/post/{created_post['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"post": created_post, "comments": [created_comment]}


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response: Response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
