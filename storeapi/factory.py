from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from . import routers
from .db import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(lifespan=lifespan)

    # Iterate through each attribute in the routers module
    for item in dir(routers):
        # Get the attribute
        attr = getattr(routers, item)
        # Check if the attribute is an instance of APIRouter and register it
        if isinstance(attr, APIRouter):
            app.include_router(attr)

    return app
