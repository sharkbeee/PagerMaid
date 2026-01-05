from pagermaid.dependence import client, scheduler, sqlite

from ._bot import bot

__all__ = [
    "bot",
    "sqlite",
    "client",
    "scheduler",
]


def get(name: str):
    data = {
        "Client": bot,
        "SqliteDict": sqlite,
        "AsyncIOScheduler": scheduler,
        "AsyncClient": client,
    }
    return data.get(name)
