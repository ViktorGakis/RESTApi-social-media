import logging
from contextlib import asynccontextmanager
from pathlib import Path

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import routers
from .db import database
from .logging_conf import configure_logging

logger: logging.Logger = logging.getLogger(__name__)


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(lifespan=lifespan)
    app.add_middleware(CorrelationIdMiddleware)
    # Iterate through each attribute in the routers module
    for item in dir(routers):
        logger.debug("item: %s", item)
        # Get the attribute
        attr = getattr(routers, item)
        # Check if the attribute is an instance of APIRouter and register it
        if isinstance(attr, APIRouter):
            app.include_router(attr)
            logger.debug("Router: %s registered", item)

    @app.exception_handler(HTTPException)
    async def http_exception_handle_logging(request, exc):
        """
        This function handles all the errors without the need to add manually logger.error
        We have used our own custom logging framework for this.
        """
        logger.error("HTTPException: %s %s", exc.status_code, exc.detail)
        return await http_exception_handler(request, exc)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    STATIC_DIR_PATH = Path(__file__).parent / "static/"
    STATIC_DIR_PATH.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR_PATH), name="static")

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # logging setup will run at startup
    # before db
    configure_logging()
    logger.info("App initializing...")
    await database.connect()
    yield
    logger.info("App terminating...")
    await database.disconnect()
