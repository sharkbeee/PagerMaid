import jwt
from fastapi import Depends, HTTPException, Request

from pagermaid.web.auth import decode_session_token
from pagermaid.web.dependencies import get_web_settings

AUTH_FAILED_DETAIL = "登录验证失败或已失效，请重新登录"


def authentication():
    def inner(request: Request):
        settings = get_web_settings(request)
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise HTTPException(status_code=401, detail=AUTH_FAILED_DETAIL)
        try:
            decode_session_token(token, settings)
        except (jwt.PyJWTError, AttributeError) as err:
            raise HTTPException(status_code=401, detail=AUTH_FAILED_DETAIL) from err

    return Depends(inner)
