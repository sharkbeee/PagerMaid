import asyncio
from types import SimpleNamespace

import pytest

from pagermaid import __main__ as main_module
from pagermaid.modules import system as system_module
from pagermaid.runtime import RuntimeLifecycle
from pagermaid.web.api import bot_info as bot_info_api


class FakeScheduler:
    def __init__(self, events, fail_shutdown=False):
        self.events = events
        self.running = False
        self.fail_shutdown = fail_shutdown

    def start(self):
        self.events.append("scheduler:start")
        self.running = True

    def shutdown(self):
        self.events.append("scheduler:shutdown")
        self.running = False
        if self.fail_shutdown:
            raise RuntimeError("scheduler failure")


class FakeWeb:
    def __init__(self, events, fail_start=False, fail_shutdown=False):
        self.events = events
        self.fail_start = fail_start
        self.fail_shutdown = fail_shutdown

    async def start(self):
        self.events.append("web:start")
        if self.fail_start:
            raise RuntimeError("web start failure")

    async def shutdown(self):
        self.events.append("web:shutdown")
        if self.fail_shutdown:
            raise RuntimeError("web shutdown failure")


class FakeBot:
    def __init__(self, events):
        self.events = events

    async def disconnect(self):
        self.events.append("bot:disconnect")


@pytest.mark.anyio
async def test_shutdown_runs_in_order_and_only_once():
    events = []
    lifecycle = RuntimeLifecycle()
    scheduler = FakeScheduler(events)
    scheduler.running = True
    web = FakeWeb(events)
    bot = FakeBot(events)
    message = object()

    async def shutdown_hooks(received_message):
        assert received_message is message
        events.append("hooks:shutdown")

    lifecycle.request_shutdown("test", message)
    await lifecycle.shutdown(scheduler, web, bot, shutdown_hooks)
    await lifecycle.shutdown(scheduler, web, bot, shutdown_hooks)

    assert events == [
        "web:shutdown",
        "scheduler:shutdown",
        "hooks:shutdown",
        "bot:disconnect",
    ]


@pytest.mark.anyio
async def test_shutdown_continues_when_components_fail(monkeypatch):
    events = []
    lifecycle = RuntimeLifecycle()
    scheduler = FakeScheduler(events, fail_shutdown=True)
    scheduler.running = True
    web = FakeWeb(events, fail_shutdown=True)
    bot = FakeBot(events)

    async def shutdown_hooks(_):
        events.append("hooks:shutdown")
        raise RuntimeError("hook failure")

    monkeypatch.setattr("pagermaid.runtime.logs.exception", lambda *_: None)

    await lifecycle.shutdown(scheduler, web, bot, shutdown_hooks)

    assert events == [
        "web:shutdown",
        "scheduler:shutdown",
        "hooks:shutdown",
        "bot:disconnect",
    ]


@pytest.mark.anyio
async def test_main_starts_and_shuts_down_runtime(monkeypatch):
    events = []
    lifecycle = RuntimeLifecycle()
    scheduler = FakeScheduler(events)
    web = FakeWeb(events)
    bot = FakeBot(events)

    async def console_bot():
        events.append("bot:start")

    async def idle(received_lifecycle):
        assert received_lifecycle is lifecycle
        events.append("runtime:idle")

    async def shutdown_hooks(_):
        events.append("hooks:shutdown")

    monkeypatch.setattr(main_module, "configure_runtime_environment", lambda: None)
    monkeypatch.setattr(main_module, "install_signal_handlers", lambda _: None)
    monkeypatch.setattr(main_module, "scheduler", scheduler)
    monkeypatch.setattr(main_module, "web", web)
    monkeypatch.setattr(main_module, "bot", bot)
    monkeypatch.setattr(main_module, "console_bot", console_bot)
    monkeypatch.setattr(main_module, "idle", idle)
    monkeypatch.setattr(main_module.HookRunner, "shutdown", shutdown_hooks)
    monkeypatch.setattr(main_module.Config, "WEB_ENABLE", False)
    monkeypatch.setattr(main_module.Config, "WEB_LOGIN", False)

    await main_module.main(lifecycle)

    assert events == [
        "scheduler:start",
        "web:start",
        "bot:start",
        "runtime:idle",
        "web:shutdown",
        "scheduler:shutdown",
        "hooks:shutdown",
        "bot:disconnect",
    ]


@pytest.mark.anyio
async def test_main_cleans_up_after_startup_failure(monkeypatch):
    events = []
    lifecycle = RuntimeLifecycle()
    scheduler = FakeScheduler(events)
    web = FakeWeb(events, fail_start=True)
    bot = FakeBot(events)

    async def shutdown_hooks(_):
        events.append("hooks:shutdown")

    monkeypatch.setattr(main_module, "configure_runtime_environment", lambda: None)
    monkeypatch.setattr(main_module, "install_signal_handlers", lambda _: None)
    monkeypatch.setattr(main_module, "scheduler", scheduler)
    monkeypatch.setattr(main_module, "web", web)
    monkeypatch.setattr(main_module, "bot", bot)
    monkeypatch.setattr(main_module.HookRunner, "shutdown", shutdown_hooks)

    with pytest.raises(RuntimeError, match="web start failure"):
        await main_module.main(lifecycle)

    assert events == [
        "scheduler:start",
        "web:start",
        "web:shutdown",
        "scheduler:shutdown",
        "hooks:shutdown",
        "bot:disconnect",
    ]


@pytest.mark.anyio
async def test_main_cleans_up_and_reraises_cancellation(monkeypatch):
    events = []
    lifecycle = RuntimeLifecycle()
    scheduler = FakeScheduler(events)
    web = FakeWeb(events)
    bot = FakeBot(events)

    async def console_bot():
        events.append("bot:start")

    async def idle(_):
        events.append("runtime:idle")
        raise asyncio.CancelledError

    async def shutdown_hooks(_):
        events.append("hooks:shutdown")

    monkeypatch.setattr(main_module, "configure_runtime_environment", lambda: None)
    monkeypatch.setattr(main_module, "install_signal_handlers", lambda _: None)
    monkeypatch.setattr(main_module, "scheduler", scheduler)
    monkeypatch.setattr(main_module, "web", web)
    monkeypatch.setattr(main_module, "bot", bot)
    monkeypatch.setattr(main_module, "console_bot", console_bot)
    monkeypatch.setattr(main_module, "idle", idle)
    monkeypatch.setattr(main_module.HookRunner, "shutdown", shutdown_hooks)
    monkeypatch.setattr(main_module.Config, "WEB_ENABLE", False)
    monkeypatch.setattr(main_module.Config, "WEB_LOGIN", False)

    with pytest.raises(asyncio.CancelledError):
        await main_module.main(lifecycle)

    assert events == [
        "scheduler:start",
        "web:start",
        "bot:start",
        "runtime:idle",
        "web:shutdown",
        "scheduler:shutdown",
        "hooks:shutdown",
        "bot:disconnect",
    ]


def test_signal_handler_requests_shutdown(monkeypatch):
    handlers = {}
    lifecycle = RuntimeLifecycle()
    monkeypatch.setattr(
        main_module,
        "signal_fn",
        lambda runtime_signal, handler: handlers.setdefault(runtime_signal, handler),
    )

    main_module.install_signal_handlers(lifecycle)
    handlers[main_module.SIGTERM](main_module.SIGTERM, None)

    assert lifecycle.shutdown_requested is True
    assert lifecycle.shutdown_reason == f"signal:{main_module.SIGTERM}"


@pytest.mark.anyio
async def test_restart_routes_request_shutdown(monkeypatch):
    telegram_lifecycle = RuntimeLifecycle()
    web_lifecycle = RuntimeLifecycle()
    edits = []
    message = SimpleNamespace(text="-restart")

    async def edit(text):
        edits.append(text)

    message.edit = edit
    monkeypatch.setattr(system_module, "lifecycle", telegram_lifecycle)
    monkeypatch.setattr(bot_info_api, "lifecycle", web_lifecycle)

    await system_module.restart.func()(message)
    response = await bot_info_api.bot_restart()

    assert telegram_lifecycle.shutdown_reason == "telegram_restart"
    assert telegram_lifecycle.shutdown_message is message
    assert web_lifecycle.shutdown_reason == "web_restart"
    assert response == {}


@pytest.mark.anyio
async def test_runtime_wait_propagates_cancellation():
    lifecycle = RuntimeLifecycle()
    task = asyncio.create_task(lifecycle.wait(asyncio.sleep(60)))
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.anyio
async def test_runtime_wait_without_service_propagates_cancellation():
    lifecycle = RuntimeLifecycle()
    task = asyncio.create_task(lifecycle.wait())
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
