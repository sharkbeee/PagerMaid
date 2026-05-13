import secrets

import pytest
from fastapi import status
from httpx import AsyncClient

from pagermaid.config import Config
from pagermaid.version import pgm_version_code


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
    cookie = r.cookies
    assert cookie.get("token_ck") is not None


@pytest.mark.anyio
async def test_command_alias_read_shape(
    client: AsyncClient,
):
    auth_token = Config.WEB_SECRET_KEY
    assert auth_token

    headers: dict[str, str] = {"token": auth_token}
    r = await client.get("/pagermaid/api/command_alias", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data.get("status") == 0
    assert data.get("msg") == "ok"
    assert isinstance(data["data"]["items"], list)

    message = secrets.token_hex(16)
    r = await client.get(
        "/pagermaid/api/test_command_alias",
        params={"message": message},
        headers=headers,
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
    auth_token = Config.WEB_SECRET_KEY
    assert auth_token

    headers: dict[str, str] = {"token": auth_token}
    r = await client.get("/pagermaid/api/get_local_plugins", headers=headers)
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
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    auth_token = Config.WEB_SECRET_KEY
    assert auth_token

    headers: dict[str, str] = {"token": auth_token}
    r = await client.get("/pagermaid/api/status", headers=headers)
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
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"

    r = await client.get("/pagermaid/api/run_sh")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("detail") == "登录验证失败或已失效，请重新登录"
