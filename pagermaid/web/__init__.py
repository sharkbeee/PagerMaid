import asyncio
import contextlib

from fastapi import FastAPI

from pagermaid.utils import logs
from pagermaid.web.app import create_app
from pagermaid.web.settings import WebSettings


class Web:
    def __init__(self):
        self.settings = WebSettings.from_legacy_config()
        self.app: FastAPI = create_app(self.settings)
        self.web_server = None
        self.web_server_task = None
        self.bot_main_task = None

    def init_web(self):
        self.settings = WebSettings.from_legacy_config()
        self.app = create_app(self.settings)

    async def start(self):
        if not self.settings.enabled:
            return
        if not self.settings.secret_key:
            logs.warning("未设置 WEB_SECRET_KEY ，请勿将 PagerMaid-Modify 暴露在公网")
        import uvicorn

        self.init_web()
        self.web_server = uvicorn.Server(
            config=uvicorn.Config(
                self.app,
                host=self.settings.host,
                port=self.settings.port,
                log_config=None,
            )
        )
        server_config = self.web_server.config
        server_config.setup_event_loop()
        if not server_config.loaded:
            server_config.load()
        self.web_server.lifespan = server_config.lifespan_class(server_config)
        try:
            await self.web_server.startup()
        except OSError as e:
            if e.errno == 10048:
                logs.error("Web Server 端口被占用：%s", e)
            logs.error("Web Server 启动失败，正在退出")
            raise SystemExit from None

        if self.web_server.should_exit:
            logs.error("Web Server 启动失败，正在退出")
            raise SystemExit from None
        logs.info("Web Server 启动成功")
        self.web_server_task = asyncio.create_task(self.web_server.main_loop())

    def stop(self):
        if self.web_server_task:
            self.web_server_task.cancel()
        if self.bot_main_task:
            self.bot_main_task.cancel()

    async def shutdown(self):
        server_task = self.web_server_task
        if server_task:
            server_task.cancel()
        try:
            if self.web_server:
                await self.web_server.shutdown()
        finally:
            try:
                if server_task:
                    with contextlib.suppress(asyncio.CancelledError):
                        await server_task
            finally:
                self.web_server_task = None
                self.web_server = None


web = Web()
