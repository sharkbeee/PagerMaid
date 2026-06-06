import asyncio
import importlib
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import pagermaid.config
import pagermaid.modules
from pagermaid.common.plugin import plugin_manager
from pagermaid.dependence import scheduler
from pagermaid.hook import HookFailure, HookRunner
from pagermaid.services import bot
from pagermaid.static import (
    all_permissions,
    help_messages,
    hook_functions,
    read_context,
)
from pagermaid.utils import lang, logs

_reload_lock = asyncio.Lock()


class RuntimeOperation(str, Enum):
    STARTUP = "startup"
    RELOAD = "reload"


class RuntimeStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    BUSY = "busy"


@dataclass(frozen=True)
class RuntimeFailure:
    stage: str
    component: str
    exception_type: str
    message: str


@dataclass
class RuntimeResult:
    operation: RuntimeOperation
    status: RuntimeStatus = RuntimeStatus.SUCCESS
    loaded_modules: List[str] = field(default_factory=list)
    loaded_plugins: List[str] = field(default_factory=list)
    failures: List[RuntimeFailure] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.status == RuntimeStatus.SUCCESS and not self.failures


def _record_exception(
    result: RuntimeResult,
    stage: str,
    component: str,
    exception: Exception,
) -> None:
    logs.exception(
        "Runtime %s failed during %s for %s: %s",
        result.operation.value,
        stage,
        component,
        exception,
    )
    result.failures.append(
        RuntimeFailure(
            stage=stage,
            component=component,
            exception_type=type(exception).__name__,
            message=str(exception),
        )
    )


def _record_hook_failures(
    result: RuntimeResult, failures: Optional[List[HookFailure]]
) -> None:
    for failure in failures or []:
        result.failures.append(
            RuntimeFailure(
                stage=f"hook:{failure.hook_type}",
                component=failure.hook_name,
                exception_type=failure.exception_type,
                message=failure.message,
            )
        )


def _complete(result: RuntimeResult) -> RuntimeResult:
    if result.failures:
        result.status = RuntimeStatus.PARTIAL_FAILURE
        logs.warning(
            "Runtime %s completed with %d failure(s): %d module(s), %d plugin(s) loaded",
            result.operation.value,
            len(result.failures),
            len(result.loaded_modules),
            len(result.loaded_plugins),
        )
    else:
        logs.info(
            "Runtime %s completed successfully: %d module(s), %d plugin(s) loaded",
            result.operation.value,
            len(result.loaded_modules),
            len(result.loaded_plugins),
        )
    return result


def reload_result_message(result: RuntimeResult) -> str:
    if result.status == RuntimeStatus.BUSY:
        return lang("reload_busy")
    if result.status == RuntimeStatus.PARTIAL_FAILURE:
        return lang("reload_partial_failure").format(count=len(result.failures))
    return lang("reload_ok")


async def _reload_all() -> RuntimeResult:
    result = RuntimeResult(operation=RuntimeOperation.RELOAD)
    _record_hook_failures(result, await HookRunner.reload_pre_exec())
    read_context.clear()
    bot._event_builders.clear()
    scheduler.remove_all_jobs()
    # init
    importlib.reload(pagermaid.config)
    importlib.reload(pagermaid.modules)
    help_messages.clear()
    all_permissions.clear()
    for functions in hook_functions.values():
        functions.clear()  # clear all hooks

    for module_name in pagermaid.modules.module_list:
        try:
            module = importlib.import_module(f"pagermaid.modules.{module_name}")
            importlib.reload(module)
            result.loaded_modules.append(module_name)
        except Exception as exception:
            _record_exception(result, "module", module_name, exception)
    for plugin_name in pagermaid.modules.plugin_list.copy():
        try:
            plugin = importlib.import_module(f"plugins.{plugin_name}")
            if os.path.exists(plugin.__file__):
                importlib.reload(plugin)
            result.loaded_plugins.append(plugin_name)
        except Exception as exception:
            _record_exception(result, "plugin", plugin_name, exception)
            pagermaid.modules.plugin_list.remove(plugin_name)
    plugin_manager.load_local_plugins()
    plugin_manager.save_local_version_map()
    _record_hook_failures(result, await HookRunner.load_success_exec())
    return _complete(result)


async def reload_all() -> RuntimeResult:
    if _reload_lock.locked():
        logs.warning("Runtime reload rejected because another reload is in progress")
        return RuntimeResult(
            operation=RuntimeOperation.RELOAD,
            status=RuntimeStatus.BUSY,
        )
    async with _reload_lock:
        return await _reload_all()


async def load_all() -> RuntimeResult:
    result = RuntimeResult(operation=RuntimeOperation.STARTUP)
    for module_name in pagermaid.modules.module_list.copy():
        try:
            importlib.import_module(f"pagermaid.modules.{module_name}")
            result.loaded_modules.append(module_name)
        except Exception as exception:
            _record_exception(result, "module", module_name, exception)
    for plugin_name in pagermaid.modules.plugin_list.copy():
        try:
            importlib.import_module(f"plugins.{plugin_name}")
            result.loaded_plugins.append(plugin_name)
        except Exception as exception:
            _record_exception(result, "plugin", plugin_name, exception)
            pagermaid.modules.plugin_list.remove(plugin_name)
    plugin_manager.load_local_plugins()
    _record_hook_failures(result, await HookRunner.load_success_exec())
    _record_hook_failures(result, await HookRunner.startup())
    return _complete(result)
