import asyncio
from os import sep
from pathlib import Path
from signal import SIGABRT, SIGINT, SIGTERM
from signal import signal as signal_fn
from sys import path, platform

from telethon.errors.rpcerrorlist import AuthKeyError

from pagermaid.common.reload import load_all
from pagermaid.config import Config
from pagermaid.dependence import scheduler
from pagermaid.hook import HookRunner
from pagermaid.runtime import lifecycle
from pagermaid.services import bot
from pagermaid.static import working_dir
from pagermaid.utils import SessionFileManager, lang, logs
from pagermaid.web import web
from pagermaid.web.api.web_login import web_login
from pyromod.methods.sign_in_qrcode import start_client


def configure_runtime_environment():
    bot.PARENT_DIR = Path(working_dir)
    plugin_path = f"{working_dir}{sep}plugins"
    if plugin_path not in path:
        path.insert(1, plugin_path)


def install_signal_handlers(runtime_lifecycle=lifecycle):
    def signal_handler(signum, _):
        runtime_lifecycle.request_shutdown(f"signal:{signum}")

    for runtime_signal in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(runtime_signal, signal_handler)


async def idle(runtime_lifecycle=lifecycle):
    while not runtime_lifecycle.shutdown_requested:
        if Config.WEB_ENABLE and Config.WEB_LOGIN:
            awaitable = asyncio.sleep(600)
        else:
            awaitable = bot._run_until_disconnected()
        await runtime_lifecycle.wait(awaitable)


async def console_bot():
    try:
        await start_client(bot)
    except AuthKeyError:
        SessionFileManager.safe_remove_session()
        raise SystemExit from None
    bot.me = await bot.get_me()
    if bot.me.bot:
        SessionFileManager.safe_remove_session()
        raise SystemExit
    logs.info(f"{lang('save_id')} {bot.me.first_name}({bot.me.id})")
    await load_all()


async def web_bot():
    try:
        await web_login.init()
    except AuthKeyError:
        SessionFileManager.safe_remove_session()
        raise SystemExit from None
    if bot.me is None:
        logs.info("Please use web to login, path: web_login .")


async def main(runtime_lifecycle=lifecycle):
    try:
        configure_runtime_environment()
        install_signal_handlers(runtime_lifecycle)
        logs.info(lang("platform") + platform + lang("platform_load"))
        if not scheduler.running:
            scheduler.start()
        await web.start()
        if not (Config.WEB_ENABLE and Config.WEB_LOGIN):
            await console_bot()
            logs.info(lang("start"))
        else:
            await web_bot()
        await idle(runtime_lifecycle)
    finally:
        await runtime_lifecycle.shutdown(scheduler, web, bot, HookRunner.shutdown)


def run():
    bot.loop.run_until_complete(main())


if __name__ == "__main__":
    run()
