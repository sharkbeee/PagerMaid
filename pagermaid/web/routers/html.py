from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from pagermaid.web.pages import admin_app, login_page

request_adaptor = """
requestAdaptor(api) {
    return api;
},
"""
response_adaptor = """
responseAdaptor(api, payload, query, request, response) {
    if (response.data.detail == '登录验证失败或已失效，请重新登录') {
        window.location.href = '/login'
        window.alert('登录验证失败或已失效，请重新登录')
    }
    return payload
},
"""
icon_path = "/static/logo.jpg"

router = APIRouter()


@router.get("/", response_class=RedirectResponse)
async def index():
    return "/admin"


@router.get("/admin", response_class=HTMLResponse)
async def admin():
    return admin_app.render(
        site_title="PagerMaid-Modify 后台管理",
        site_icon=icon_path,
        requestAdaptor=request_adaptor,
        responseAdaptor=response_adaptor,
    )


@router.get("/login", response_class=HTMLResponse)
async def login():
    return login_page.render(
        site_title="登录 | PagerMaid-Modify 后台管理",
        site_icon=icon_path,
    )
