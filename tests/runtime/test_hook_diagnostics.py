import asyncio
from types import SimpleNamespace

import pytest

from pagermaid import hook as hook_module
from pagermaid import listener as listener_module
from pagermaid.hook import HookRunner


@pytest.mark.anyio
async def test_hook_runner_isolates_failures_and_returns_failure_details(
    monkeypatch,
):
    events = []
    log_messages = []

    async def first_hook():
        events.append("first")

    async def failing_hook():
        events.append("failing")
        raise RuntimeError("hook failed")

    async def later_hook():
        events.append("later")

    monkeypatch.setitem(
        hook_module.hook_functions,
        "startup",
        {first_hook, failing_hook, later_hook},
    )
    monkeypatch.setattr(
        hook_module.logs,
        "exception",
        lambda message, *args: log_messages.append(message % args),
    )

    failures = await HookRunner.startup()

    assert set(events) == {"first", "failing", "later"}
    assert len(failures) == 1
    assert failures[0].hook_type == "startup"
    assert failures[0].hook_name.endswith(".failing_hook")
    assert failures[0].exception_type == "RuntimeError"
    assert failures[0].message == "hook failed"
    assert log_messages == [
        f"Hook startup {failures[0].hook_name} failed: hook failed",
    ]


@pytest.mark.anyio
async def test_hook_runner_does_not_swallow_cancellation(monkeypatch):
    async def cancelled_hook():
        raise asyncio.CancelledError

    monkeypatch.setitem(hook_module.hook_functions, "startup", {cancelled_hook})

    with pytest.raises(asyncio.CancelledError):
        await HookRunner.startup()


@pytest.mark.anyio
async def test_command_errors_are_logged_when_diagnostics_are_disabled(monkeypatch):
    log_messages = []
    process_error_calls = []

    async def failing_command():
        raise RuntimeError("command failed")

    async def process_error(*args, **kwargs):
        process_error_calls.append((args, kwargs))

    monkeypatch.setattr(
        listener_module.ignore_groups_manager, "check_id", lambda _: False
    )
    monkeypatch.setattr(listener_module.bot, "add_event_handler", lambda *_: None)
    monkeypatch.setattr(
        listener_module.logs, "error", lambda message: log_messages.append(message)
    )
    monkeypatch.setattr(listener_module.HookRunner, "process_error_exec", process_error)

    command = listener_module.listener(diagnostics=False, ignore_edited=True)(
        failing_command
    )
    context = SimpleNamespace(
        is_group=False,
        is_private=True,
        via_bot_id=None,
        forward=None,
        chat_id=1,
        id=2,
        sender_id=3,
        text="test command",
    )

    async def edit(*args, **kwargs):
        return None

    context.edit = edit

    await command.get_handler()(context)

    assert len(log_messages) == 1
    assert "RuntimeError: command failed" in log_messages[0]
    assert process_error_calls == []
