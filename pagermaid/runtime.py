import asyncio
from typing import Awaitable, Callable, Optional

from pagermaid.utils import logs


class RuntimeLifecycle:
    def __init__(self):
        self.shutdown_requested = False
        self.shutdown_reason: Optional[str] = None
        self.shutdown_message = None
        self._shutdown_event: Optional[asyncio.Event] = None
        self._shutdown_lock: Optional[asyncio.Lock] = None
        self._shutdown_complete = False

    def _event(self) -> asyncio.Event:
        if self._shutdown_event is None:
            self._shutdown_event = asyncio.Event()
            if self.shutdown_requested:
                self._shutdown_event.set()
        return self._shutdown_event

    def _lock(self) -> asyncio.Lock:
        if self._shutdown_lock is None:
            self._shutdown_lock = asyncio.Lock()
        return self._shutdown_lock

    def request_shutdown(self, reason: str, message=None) -> bool:
        first_request = not self.shutdown_requested
        if first_request:
            self.shutdown_reason = reason
        if message is not None and self.shutdown_message is None:
            self.shutdown_message = message
        self.shutdown_requested = True
        if self._shutdown_event is not None:
            self._shutdown_event.set()
        return first_request

    async def wait(self, awaitable: Optional[Awaitable] = None) -> None:
        if self.shutdown_requested:
            return
        shutdown_task = asyncio.create_task(self._event().wait())
        if awaitable is None:
            try:
                await shutdown_task
            finally:
                if not shutdown_task.done():
                    shutdown_task.cancel()
                await asyncio.gather(shutdown_task, return_exceptions=True)
            return

        runtime_task = asyncio.create_task(awaitable)
        tasks = {shutdown_task, runtime_task}
        try:
            done, _ = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if runtime_task in done:
                await runtime_task
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_async_cleanup(self, name: str, cleanup: Callable[[], Awaitable]):
        try:
            await cleanup()
        except Exception:
            logs.exception("Runtime shutdown failed while stopping %s", name)

    def _run_sync_cleanup(self, name: str, cleanup: Callable[[], None]):
        try:
            cleanup()
        except Exception:
            logs.exception("Runtime shutdown failed while stopping %s", name)

    async def shutdown(self, scheduler, web, bot, shutdown_hooks) -> None:
        async with self._lock():
            if self._shutdown_complete:
                return

            await self._run_async_cleanup("web", web.shutdown)
            self._run_sync_cleanup(
                "scheduler",
                lambda: scheduler.shutdown() if scheduler.running else None,
            )
            await self._run_async_cleanup(
                "shutdown hooks",
                lambda: shutdown_hooks(self.shutdown_message),
            )
            await self._run_async_cleanup("bot", bot.disconnect)
            self._shutdown_complete = True


lifecycle = RuntimeLifecycle()
