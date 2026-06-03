from fastapi import APIRouter

from pagermaid.web.routers.api import router as api_router
from pagermaid.web.routers.html import router as html_router

__all__ = ["create_router"]


def create_router() -> APIRouter:
    router = APIRouter()
    router.include_router(api_router)
    router.include_router(html_router)
    return router
