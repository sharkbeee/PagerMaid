from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from pagermaid.web.app import create_app
from pagermaid.web.settings import WebSettings


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    return create_app(WebSettings.from_legacy_config())


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
