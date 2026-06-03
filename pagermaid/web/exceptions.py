from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def web_http_exception_handler(
        request: Request, exc: HTTPException
    ) -> Response:
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def web_request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> Response:
        return await request_validation_exception_handler(request, exc)
