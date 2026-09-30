from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings

API_V1_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or get_settings()
    is_development = configuration.app_env == "development"

    application = FastAPI(
        title=configuration.app_name,
        version=__version__,
        docs_url="/docs" if is_development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if is_development else None,
    )
    application.include_router(api_router, prefix=API_V1_PREFIX)
    return application


app = create_app()
