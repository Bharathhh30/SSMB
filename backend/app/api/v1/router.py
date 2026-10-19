from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.features.auth.router import router as auth_router
from app.features.communities.router import router as communities_router
from app.features.communities.topics_router import router as topics_router
from app.features.profiles.router import router as profiles_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(topics_router)
api_router.include_router(communities_router)
api_router.include_router(profiles_router)
