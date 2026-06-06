from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.types import Scope

from pagermaid.web.exceptions import register_exception_handlers
from pagermaid.web.lifespan import lifespan
from pagermaid.web.routers import create_router
from pagermaid.web.settings import WebSettings

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


class BrandingStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        if path != "logo.jpg":
            raise HTTPException(status_code=404)
        return await super().get_response(path, scope)


def create_app(settings: WebSettings | None = None) -> FastAPI:
    settings = settings or WebSettings.from_legacy_config()
    app = FastAPI(lifespan=lifespan)
    app.state.web_settings = settings

    register_exception_handlers(app)
    app.mount("/static", BrandingStaticFiles(directory=ASSETS_DIR), name="static")
    app.include_router(create_router())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
