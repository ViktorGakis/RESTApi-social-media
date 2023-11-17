from fastapi import APIRouter, FastAPI

from . import routers


def create_app():
    app: FastAPI = FastAPI()

    # Iterate through each attribute in the routers module
    for item in dir(routers):
        # Get the attribute
        attr = getattr(routers, item)
        # Check if the attribute is an instance of APIRouter and register it
        if isinstance(attr, APIRouter):
            app.include_router(attr)

    return app
