from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.db.engine import create_database_engine

API_V1_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or get_settings()
    is_development = configuration.app_env == "development"

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database_engine = create_database_engine(configuration.database_url)
        application.state.database_engine = database_engine
        try:
            yield
        finally:
            if database_engine is not None:
                await database_engine.dispose()
            application.state.database_engine = None

    application = FastAPI(
        title=configuration.app_name,
        version=__version__,
        docs_url="/docs" if is_development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if is_development else None,
        lifespan=lifespan,
    )
    application.state.database_engine = None
    application.include_router(api_router, prefix=API_V1_PREFIX)
    return application


app = create_app()
