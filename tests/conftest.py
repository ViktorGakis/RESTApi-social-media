from os import environ
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from httpx import AsyncClient

# from storeapi import create_app


# ---- Alternative way to import without factory
# from ..routers.main.routers import comment_table, post_table
# app = create_app()

# ---- ENV CHANGE FOR TEST!
# first we change the STATE
# then we import app
# because app calls db
# and db reads config
environ["ENV_STATE"] = "test"
# then the app is initiallized
from main import app

# db should be called first
from RESTApi.db import database, user_table


# async platform needed for pytest
# this is practically saying use asyncio
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    db_file_path = Path(environ["DEV_DATABASE_URL"].split("///")[-1])

    if db_file_path.exists():
        db_file_path.unlink()
        print("TEST DB DELETED")

    await database.connect()
    # post_table.clear()
    # comment_table.clear()
    yield
    await database.disconnect()


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details: dict[str, str] = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict):
    response: Response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
