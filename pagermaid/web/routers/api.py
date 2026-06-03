from fastapi import APIRouter

from pagermaid.web.api import base_api_router, base_html_router

router = APIRouter()
router.include_router(base_api_router)
router.include_router(base_html_router)
