from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
