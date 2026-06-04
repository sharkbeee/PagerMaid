from fastapi import Request

from pagermaid.web.settings import WebSettings


def get_web_settings(request: Request) -> WebSettings:
    return request.app.state.web_settings
