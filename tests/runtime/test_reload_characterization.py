import asyncio
from types import SimpleNamespace

import pytest

from pagermaid.common import reload as runtime_reload
from pagermaid.hook import HookFailure


class ClearRecorder:
    def __init__(self, name, events):
        self.name = name
        self.events = events

    def clear(self):
        self.events.append(f"clear:{self.name}")


@pytest.mark.anyio
async def test_load_all_continues_after_failures_and_runs_startup_hooks(monkeypatch):
    events = []
    modules = SimpleNamespace(
        module_list=["module_ok", "module_bad", "module_later"],
        plugin_list=["plugin_ok", "plugin_bad", "plugin_later"],
    )
    monkeypatch.setattr(runtime_reload.pagermaid, "modules", modules)

    def import_module(name):
        events.append(f"import:{name}")
        if name in {"pagermaid.modules.module_bad", "plugins.plugin_bad"}:
            raise RuntimeError(f"failed to import {name}")
        return SimpleNamespace(__name__=name)

    async def load_success():
        events.append("hook:load_success")

    async def startup():
        events.append("hook:startup")

    monkeypatch.setattr(runtime_reload.importlib, "import_module", import_module)
    monkeypatch.setattr(
        runtime_reload.plugin_manager,
        "load_local_plugins",
        lambda: events.append("plugin_manager:load_local_plugins"),
    )
    monkeypatch.setattr(runtime_reload.HookRunner, "load_success_exec", load_success)
    monkeypatch.setattr(runtime_reload.HookRunner, "startup", startup)

    result = await runtime_reload.load_all()

    assert events == [
        "import:pagermaid.modules.module_ok",
        "import:pagermaid.modules.module_bad",
        "import:pagermaid.modules.module_later",
        "import:plugins.plugin_ok",
        "import:plugins.plugin_bad",
        "import:plugins.plugin_later",
        "plugin_manager:load_local_plugins",
        "hook:load_success",
        "hook:startup",
    ]
    assert modules.module_list == ["module_ok", "module_bad", "module_later"]
    assert modules.plugin_list == ["plugin_ok", "plugin_later"]
    assert result.operation == runtime_reload.RuntimeOperation.STARTUP
    assert result.status == runtime_reload.RuntimeStatus.PARTIAL_FAILURE
    assert result.succeeded is False
    assert result.loaded_modules == ["module_ok", "module_later"]
    assert result.loaded_plugins == ["plugin_ok", "plugin_later"]
    assert [
        (failure.stage, failure.component, failure.exception_type)
        for failure in result.failures
    ] == [
        ("module", "module_bad", "RuntimeError"),
        ("plugin", "plugin_bad", "RuntimeError"),
    ]


@pytest.mark.anyio
async def test_reload_all_clears_state_before_reloading_and_runs_reload_hooks(
    monkeypatch,
):
    events = []
    config = SimpleNamespace(__name__="pagermaid.config")
    modules = SimpleNamespace(
        __name__="pagermaid.modules",
        module_list=["module_ok"],
        plugin_list=["plugin_ok"],
    )
    monkeypatch.setattr(runtime_reload.pagermaid, "config", config)
    monkeypatch.setattr(runtime_reload.pagermaid, "modules", modules)
    monkeypatch.setattr(
        runtime_reload, "read_context", ClearRecorder("read_context", events)
    )
    monkeypatch.setattr(
        runtime_reload,
        "bot",
        SimpleNamespace(_event_builders=ClearRecorder("event_builders", events)),
    )
    monkeypatch.setattr(
        runtime_reload,
        "scheduler",
        SimpleNamespace(
            remove_all_jobs=lambda: events.append("scheduler:remove_all_jobs")
        ),
    )
    monkeypatch.setattr(
        runtime_reload, "help_messages", ClearRecorder("help_messages", events)
    )
    monkeypatch.setattr(
        runtime_reload, "all_permissions", ClearRecorder("all_permissions", events)
    )
    monkeypatch.setattr(
        runtime_reload,
        "hook_functions",
        {
            "startup": ClearRecorder("hook_functions:startup", events),
            "reload_pre": ClearRecorder("hook_functions:reload_pre", events),
        },
    )

    async def reload_pre():
        events.append("hook:reload_pre")

    async def load_success():
        events.append("hook:load_success")

    def import_module(name):
        events.append(f"import:{name}")
        return SimpleNamespace(__name__=name, __file__=f"/tmp/{name}.py")

    def reload_module(module):
        events.append(f"reload:{module.__name__}")
        return module

    monkeypatch.setattr(runtime_reload.HookRunner, "reload_pre_exec", reload_pre)
    monkeypatch.setattr(runtime_reload.HookRunner, "load_success_exec", load_success)
    monkeypatch.setattr(runtime_reload.importlib, "import_module", import_module)
    monkeypatch.setattr(runtime_reload.importlib, "reload", reload_module)
    monkeypatch.setattr(runtime_reload.os.path, "exists", lambda _: True)
    monkeypatch.setattr(
        runtime_reload.plugin_manager,
        "load_local_plugins",
        lambda: events.append("plugin_manager:load_local_plugins"),
    )
    monkeypatch.setattr(
        runtime_reload.plugin_manager,
        "save_local_version_map",
        lambda: events.append("plugin_manager:save_local_version_map"),
    )

    result = await runtime_reload.reload_all()

    assert events == [
        "hook:reload_pre",
        "clear:read_context",
        "clear:event_builders",
        "scheduler:remove_all_jobs",
        "reload:pagermaid.config",
        "reload:pagermaid.modules",
        "clear:help_messages",
        "clear:all_permissions",
        "clear:hook_functions:startup",
        "clear:hook_functions:reload_pre",
        "import:pagermaid.modules.module_ok",
        "reload:pagermaid.modules.module_ok",
        "import:plugins.plugin_ok",
        "reload:plugins.plugin_ok",
        "plugin_manager:load_local_plugins",
        "plugin_manager:save_local_version_map",
        "hook:load_success",
    ]
    assert result.operation == runtime_reload.RuntimeOperation.RELOAD
    assert result.status == runtime_reload.RuntimeStatus.SUCCESS
    assert result.succeeded is True
    assert result.loaded_modules == ["module_ok"]
    assert result.loaded_plugins == ["plugin_ok"]
    assert result.failures == []


@pytest.mark.anyio
async def test_load_all_includes_hook_failures_in_result(monkeypatch):
    modules = SimpleNamespace(module_list=[], plugin_list=[])
    monkeypatch.setattr(runtime_reload.pagermaid, "modules", modules)
    monkeypatch.setattr(
        runtime_reload.plugin_manager, "load_local_plugins", lambda: None
    )

    async def load_success():
        return [
            HookFailure(
                hook_type="load_success",
                hook_name="plugins.example.after_load",
                exception_type="RuntimeError",
                message="hook failed",
            )
        ]

    async def startup():
        return []

    monkeypatch.setattr(runtime_reload.HookRunner, "load_success_exec", load_success)
    monkeypatch.setattr(runtime_reload.HookRunner, "startup", startup)

    result = await runtime_reload.load_all()

    assert result.status == runtime_reload.RuntimeStatus.PARTIAL_FAILURE
    assert result.succeeded is False
    assert result.failures == [
        runtime_reload.RuntimeFailure(
            stage="hook:load_success",
            component="plugins.example.after_load",
            exception_type="RuntimeError",
            message="hook failed",
        )
    ]


@pytest.mark.anyio
async def test_load_all_does_not_swallow_cancellation(monkeypatch):
    modules = SimpleNamespace(module_list=["cancelled"], plugin_list=[])
    monkeypatch.setattr(runtime_reload.pagermaid, "modules", modules)

    def import_module(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(runtime_reload.importlib, "import_module", import_module)

    with pytest.raises(asyncio.CancelledError):
        await runtime_reload.load_all()


@pytest.mark.anyio
async def test_reload_all_rejects_concurrent_reload(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def blocked_reload():
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return runtime_reload.RuntimeResult(
            operation=runtime_reload.RuntimeOperation.RELOAD
        )

    monkeypatch.setattr(runtime_reload, "_reload_all", blocked_reload)

    first_reload = asyncio.create_task(runtime_reload.reload_all())
    await started.wait()
    busy_result = await runtime_reload.reload_all()
    release.set()
    first_result = await first_reload

    assert calls == 1
    assert first_result.succeeded is True
    assert busy_result.operation == runtime_reload.RuntimeOperation.RELOAD
    assert busy_result.status == runtime_reload.RuntimeStatus.BUSY
    assert busy_result.succeeded is False


def test_reload_result_message_describes_busy_and_partial_failure(monkeypatch):
    messages = {
        "reload_busy": "busy",
        "reload_partial_failure": "partial: {count}",
        "reload_ok": "success",
    }
    monkeypatch.setattr(runtime_reload, "lang", messages.__getitem__)

    busy = runtime_reload.RuntimeResult(
        operation=runtime_reload.RuntimeOperation.RELOAD,
        status=runtime_reload.RuntimeStatus.BUSY,
    )
    partial = runtime_reload.RuntimeResult(
        operation=runtime_reload.RuntimeOperation.RELOAD,
        status=runtime_reload.RuntimeStatus.PARTIAL_FAILURE,
        failures=[
            runtime_reload.RuntimeFailure(
                stage="plugin",
                component="broken",
                exception_type="RuntimeError",
                message="failed",
            )
        ],
    )
    success = runtime_reload.RuntimeResult(
        operation=runtime_reload.RuntimeOperation.RELOAD
    )

    assert runtime_reload.reload_result_message(busy) == "busy"
    assert runtime_reload.reload_result_message(partial) == "partial: 1"
    assert runtime_reload.reload_result_message(success) == "success"
