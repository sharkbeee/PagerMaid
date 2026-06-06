from types import SimpleNamespace

import pytest

from pagermaid.common import reload as runtime_reload


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

    await runtime_reload.load_all()

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

    await runtime_reload.reload_all()

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
