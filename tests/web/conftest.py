from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from pagermaid.web import web


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def init_web():
    web.init_web()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=web.app),
        base_url="http://test",
    ) as ac:
        yield ac
