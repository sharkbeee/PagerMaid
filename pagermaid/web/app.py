from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from pagermaid.web.api import base_api_router, base_html_router
from pagermaid.web.lifespan import lifespan
from pagermaid.web.routers import html_router
from pagermaid.web.settings import WebSettings


def create_app(settings: WebSettings | None = None) -> FastAPI:
    settings = settings or WebSettings.from_legacy_config()
    app = FastAPI(lifespan=lifespan)

    app.include_router(base_api_router)
    app.include_router(base_html_router)
    app.include_router(html_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
