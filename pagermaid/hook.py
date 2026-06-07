import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional

from telethon.events import StopPropagation

from pagermaid.inject import inject
from pagermaid.static import hook_functions
from pagermaid.utils import logs

if TYPE_CHECKING:
    from pagermaid.enums import Message


@dataclass(frozen=True)
class HookFailure:
    hook_type: str
    hook_name: str
    exception_type: str
    message: str


class Hook:
    @staticmethod
    def on_startup():
        """
        注册一个启动钩子
        """

        def decorator(function):
            hook_functions["startup"].add(function)
            return function

        return decorator

    @staticmethod
    def on_shutdown():
        """
        注册一个关闭钩子
        """

        def decorator(function):
            hook_functions["shutdown"].add(function)
            return function

        return decorator

    @staticmethod
    def command_preprocessor():
        """
        注册一个命令预处理钩子
        """

        def decorator(function):
            hook_functions["command_pre"].add(function)
            return function

        return decorator

    @staticmethod
    def command_postprocessor():
        """
        注册一个命令后处理钩子
        """

        def decorator(function):
            hook_functions["command_post"].add(function)
            return function

        return decorator

    @staticmethod
    def process_error():
        """
        注册一个错误处理钩子
        """

        def decorator(function):
            hook_functions["process_error"].add(function)
            return function

        return decorator

    @staticmethod
    def load_success():
        """
        注册一个插件加载完成钩子
        """

        def decorator(function):
            hook_functions["load_plugins_finished"].add(function)
            return function

        return decorator

    @staticmethod
    def reload_preprocessor():
        """
        注册一个插件重载前处理钩子
        """

        def decorator(function):
            hook_functions["reload_pre"].add(function)
            return function

        return decorator


class HookRunner:
    @staticmethod
    def _hook_name(function: Callable) -> str:
        module = getattr(function, "__module__", "")
        name = getattr(function, "__qualname__", repr(function))
        return f"{module}.{name}" if module else name

    @staticmethod
    async def _run_hook(
        hook_type: str,
        function: Callable,
        message: Optional["Message"],
        **data,
    ) -> Optional[HookFailure]:
        hook_name = HookRunner._hook_name(function)
        try:
            await function(**inject(message, function, **data))
        except StopPropagation:
            raise
        except Exception as exception:
            logs.exception("Hook %s %s failed: %s", hook_type, hook_name, exception)
            return HookFailure(
                hook_type=hook_type,
                hook_name=hook_name,
                exception_type=type(exception).__name__,
                message=str(exception),
            )
        return None

    @staticmethod
    async def _run_hooks(
        hook_type: str,
        functions,
        message: Optional["Message"] = None,
        **data,
    ) -> List[HookFailure]:
        results = await asyncio.gather(
            *[
                HookRunner._run_hook(hook_type, function, message, **data)
                for function in functions
            ]
        )
        return [result for result in results if result is not None]

    @staticmethod
    async def startup() -> List[HookFailure]:
        return await HookRunner._run_hooks("startup", hook_functions["startup"])

    @staticmethod
    async def shutdown(message: Optional["Message"] = None) -> List[HookFailure]:
        return await HookRunner._run_hooks(
            "shutdown", hook_functions["shutdown"], message=message
        )

    @staticmethod
    async def command_pre(
        message: "Message", command, sub_command
    ) -> List[HookFailure]:
        return await HookRunner._run_hooks(
            "command_pre",
            hook_functions["command_pre"],
            message=message,
            command=command,
            sub_command=sub_command,
        )

    @staticmethod
    async def command_post(
        message: "Message", command, sub_command
    ) -> List[HookFailure]:
        return await HookRunner._run_hooks(
            "command_post",
            hook_functions["command_post"],
            message=message,
            command=command,
            sub_command=sub_command,
        )

    @staticmethod
    async def process_error_exec(
        message: "Message", command, exc_info: BaseException, exc_format: str
    ) -> List[HookFailure]:
        return await HookRunner._run_hooks(
            "process_error",
            hook_functions["process_error"],
            message=message,
            command=command,
            exc_info=exc_info,
            exc_format=exc_format,
        )

    @staticmethod
    async def load_success_exec() -> List[HookFailure]:
        return await HookRunner._run_hooks(
            "load_success", hook_functions["load_plugins_finished"]
        )

    @staticmethod
    async def reload_pre_exec() -> List[HookFailure]:
        return await HookRunner._run_hooks("reload_pre", hook_functions["reload_pre"])
