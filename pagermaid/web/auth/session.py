import datetime
from typing import Any

import jwt
from starlette.responses import Response

from pagermaid.web.settings import WebSettings

ALGORITHM = "HS256"
SESSION_TOKEN_TYPE = "web_session"


def create_session_token(settings: WebSettings) -> str:
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.session_ttl_minutes
    )
    data = {
        "exp": expires_at,
        "type": SESSION_TOKEN_TYPE,
    }
    return jwt.encode(data, settings.secret_key, algorithm=ALGORITHM)


def decode_session_token(token: str, settings: WebSettings) -> dict[str, Any]:
    data = jwt.decode(token, settings.secret_key, algorithms=ALGORITHM)
    if data.get("type") != SESSION_TOKEN_TYPE:
        raise jwt.InvalidTokenError("invalid token type")
    return data


def set_session_cookie(response: Response, token: str, settings: WebSettings) -> None:
    max_age = settings.session_ttl_minutes * 60
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


def clear_session_cookie(response: Response, settings: WebSettings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
