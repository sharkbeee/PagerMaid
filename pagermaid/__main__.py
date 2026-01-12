import asyncio
import contextlib
from os import sep
from pathlib import Path
from signal import SIGABRT, SIGINT, SIGTERM
from signal import signal as signal_fn
from sys import exit, path, platform

from telethon.errors.rpcerrorlist import AuthKeyError

from pagermaid.common.reload import load_all
from pagermaid.config import Config
from pagermaid.dependence import scheduler
from pagermaid.services import bot
from pagermaid.static import working_dir
from pagermaid.utils import SessionFileManager, lang, logs
from pagermaid.web import web
from pagermaid.web.api.web_login import web_login
from pyromod.methods.sign_in_qrcode import start_client

bot.PARENT_DIR = Path(working_dir)
path.insert(1, f"{working_dir}{sep}plugins")


async def idle():
    task = None

    def signal_handler(_, __):
        if web.web_server_task:
            web.web_server_task.cancel()
        task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)

    while True:
        if Config.WEB_ENABLE and Config.WEB_LOGIN:
            t = asyncio.sleep(600)
        else:
            t = bot._run_until_disconnected()
        task = asyncio.create_task(t)
        web.bot_main_task = task
        try:
            await task
        except asyncio.CancelledError:
            break


async def console_bot():
    try:
        await start_client(bot)
    except AuthKeyError:
        SessionFileManager.safe_remove_session()
        exit()
    bot.me = await bot.get_me()
    if bot.me.bot:
        SessionFileManager.safe_remove_session()
        exit()
    logs.info(f"{lang('save_id')} {bot.me.first_name}({bot.me.id})")
    await load_all()


async def web_bot():
    try:
        await web_login.init()
    except AuthKeyError:
        SessionFileManager.safe_remove_session()
        exit()
    if bot.me is None:
        logs.info("Please use web to login, path: web_login .")


async def main():
    logs.info(lang("platform") + platform + lang("platform_load"))
    if not scheduler.running:
        scheduler.start()
    await web.start()
    if not (Config.WEB_ENABLE and Config.WEB_LOGIN):
        await console_bot()
        logs.info(lang("start"))
    else:
        await web_bot()
    try:
        await idle()
    finally:
        if scheduler.running:
            scheduler.shutdown()
        with contextlib.suppress(ConnectionError):
            await bot.disconnect()
        if web.web_server:
            with contextlib.suppress(AttributeError):
                await web.web_server.shutdown()


bot.loop.run_until_complete(main())
