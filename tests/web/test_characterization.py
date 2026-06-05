import secrets

import pytest
from fastapi import status
from httpx import AsyncClient

from pagermaid.config import Config
from pagermaid.version import pgm_version_code


async def login_client(client: AsyncClient):
    return await client.post(
        "/pagermaid/api/login", json={"password": Config.WEB_SECRET_KEY}
    )


@pytest.mark.anyio
async def test_root_route_redirect(client: AsyncClient):
    r = await client.get("/", follow_redirects=False)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert r.headers["location"] == "/admin"


@pytest.mark.anyio
async def test_login_page(client: AsyncClient):
    r = await client.get("/login")
    assert r.status_code == status.HTTP_200_OK
    assert "登录 | PagerMaid-Modify 后台管理" in r.text


@pytest.mark.anyio
async def test_login_success_and_failure(client: AsyncClient):
    r = await client.post(
        "/pagermaid/api/login", json={"password": secrets.token_hex(32)}
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == -100
    assert data.get("msg") == "登录失败，请重新输入密钥"
    assert data.get("data") is None

    r = await client.post(
        "/pagermaid/api/login", json={"password": Config.WEB_SECRET_KEY}
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "登录成功"
    assert data.get("data").get("version") == pgm_version_code
    assert data.get("data").get("token") is None
    cookie = r.cookies
    assert cookie.get("token_ck") is not None
    set_cookie = r.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


@pytest.mark.anyio
async def test_command_alias_read_shape(
    client: AsyncClient,
):
    r = await login_client(client)
    assert r.status_code == status.HTTP_200_OK

    r = await client.get("/pagermaid/api/command_alias")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "ok"
    assert isinstance(data["data"]["items"], list)

    message = secrets.token_hex(16)
    r = await client.get(
        "/pagermaid/api/test_command_alias",
        params={"message": message},
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "测试成功"
    assert data["data"]["new_msg"] == message


@pytest.mark.anyio
async def test_local_plugin_list_shape(
    client: AsyncClient,
):
    r = await login_client(client)
    assert r.status_code == status.HTTP_200_OK

    r = await client.get("/pagermaid/api/get_local_plugins")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "ok"
    assert isinstance(data["data"]["rows"], list)
    assert isinstance(data["data"]["total"], int)
    assert data["data"]["total"] == len(data["data"]["rows"])


@pytest.mark.anyio
async def test_status_shape_requires_auth_and_returns_expected_keys(
    client: AsyncClient,
):
    r = await client.get("/pagermaid/api/status")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    r = await client.get(
        "/pagermaid/api/status", headers={"token": Config.WEB_SECRET_KEY}
    )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    r = await login_client(client)
    assert r.status_code == status.HTTP_200_OK

    r = await client.get("/pagermaid/api/status")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    keys = [
        "version",
        "run_time",
        "cpu_percent",
        "ram_percent",
        "swap_percent",
        "process_cpu_percent",
        "process_ram_percent",
    ]
    for key in keys:
        assert key in data


@pytest.mark.anyio
async def test_dangerous_endpoints_are_auth_gated(
    client: AsyncClient,
):
    r = await client.get("/pagermaid/api/run_eval")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    r = await client.get("/pagermaid/api/run_sh")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"


@pytest.mark.anyio
async def test_dangerous_endpoints_are_disabled_by_default(
    client: AsyncClient,
):
    r = await login_client(client)
    assert r.status_code == status.HTTP_200_OK

    r = await client.get("/pagermaid/api/run_eval")
    assert r.status_code == status.HTTP_404_NOT_FOUND

    r = await client.get("/pagermaid/api/run_sh")
    assert r.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_admin_page_does_not_expose_dangerous_endpoint_references(
    client: AsyncClient,
):
    r = await client.get("/admin")
    assert r.status_code == status.HTTP_200_OK
    assert "/pagermaid/api/run_eval" not in r.text
    assert "/pagermaid/api/run_sh" not in r.text


@pytest.mark.anyio
async def test_session_check_and_logout(client: AsyncClient):
    r = await client.get("/pagermaid/api/session-check")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    r = await login_client(client)
    assert r.status_code == status.HTTP_200_OK

    r = await client.get("/pagermaid/api/session-check")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "ok"

    r = await client.post("/pagermaid/api/logout")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "退出登录成功"

    r = await client.get("/pagermaid/api/session-check")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"
