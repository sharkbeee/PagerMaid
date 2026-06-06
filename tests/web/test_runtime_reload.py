import pytest

import pagermaid.web.api.command_alias as command_alias_api
import pagermaid.web.api.plugin as plugin_api
from pagermaid.common.reload import (
    RuntimeFailure,
    RuntimeOperation,
    RuntimeResult,
    RuntimeStatus,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "result",
    [
        RuntimeResult(
            operation=RuntimeOperation.RELOAD,
            status=RuntimeStatus.BUSY,
        ),
        RuntimeResult(
            operation=RuntimeOperation.RELOAD,
            status=RuntimeStatus.PARTIAL_FAILURE,
            failures=[
                RuntimeFailure(
                    stage="plugin",
                    component="broken",
                    exception_type="RuntimeError",
                    message="failed",
                )
            ],
        ),
    ],
)
async def test_reload_error_response_uses_nonzero_envelope(monkeypatch, result):
    async def reload_all():
        return result

    monkeypatch.setattr(plugin_api, "reload_all", reload_all)
    monkeypatch.setattr(plugin_api, "reload_result_message", lambda _: "reload failed")

    response = await plugin_api.reload_error_response()

    assert response == {"status": -100, "msg": "reload failed"}


@pytest.mark.anyio
async def test_reload_error_response_returns_none_on_success(monkeypatch):
    async def reload_all():
        return RuntimeResult(operation=RuntimeOperation.RELOAD)

    monkeypatch.setattr(plugin_api, "reload_all", reload_all)

    assert await plugin_api.reload_error_response() is None


@pytest.mark.anyio
async def test_command_alias_returns_nonzero_envelope_when_reload_is_busy(monkeypatch):
    async def save_from_web(_):
        return RuntimeResult(
            operation=RuntimeOperation.RELOAD,
            status=RuntimeStatus.BUSY,
        )

    monkeypatch.setattr(command_alias_api.AliasManager, "save_from_web", save_from_web)
    monkeypatch.setattr(
        command_alias_api, "reload_result_message", lambda _: "reload busy"
    )

    response = await command_alias_api.add_command_alias({"items": []})

    assert response == {"status": 1, "msg": "reload busy"}
