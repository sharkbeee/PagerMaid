from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from pagermaid.web.exceptions import register_exception_handlers
from pagermaid.web.lifespan import lifespan
from pagermaid.web.routers import create_router
from pagermaid.web.settings import WebSettings


def create_app(settings: WebSettings | None = None) -> FastAPI:
    settings = settings or WebSettings.from_legacy_config()
    app = FastAPI(lifespan=lifespan)
    app.state.web_settings = settings

    register_exception_handlers(app)
    app.include_router(create_router())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
