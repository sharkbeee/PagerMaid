import secrets
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pagermaid.version import pgm_version_code
from pagermaid.web.api.utils import authentication
from pagermaid.web.auth import (
    clear_session_cookie,
    create_session_token,
    set_session_cookie,
)
from pagermaid.web.dependencies import get_web_settings


class UserModel(BaseModel):
    password: Optional[str] = None


route = APIRouter()


@route.post("/login", response_class=JSONResponse)
async def login(request: Request, user: UserModel):
    settings = get_web_settings(request)
    password = user.password or ""
    secret_key = settings.secret_key or ""
    if secret_key and secrets.compare_digest(password, secret_key):
        token = create_session_token(settings)
        data = {
            "status": 0,
            "msg": "登录成功",
            "data": {"version": pgm_version_code},
        }
        response = JSONResponse(content=data)
        set_session_cookie(response, token, settings)
        return response
    return {"status": -100, "msg": "登录失败，请重新输入密钥"}


@route.post("/logout", response_class=JSONResponse)
async def logout(request: Request):
    settings = get_web_settings(request)
    response = JSONResponse(content={"status": 0, "msg": "退出登录成功"})
    clear_session_cookie(response, settings)
    return response


@route.get(
    "/session-check", response_class=JSONResponse, dependencies=[authentication()]
)
async def session_check():
    return {"status": 0, "msg": "ok"}
