from telethon import TelegramClient
from yaml import FullLoader, load

with open(r"config.yml") as cfg:
    config = load(cfg, Loader=FullLoader)
api_key = config["api_key"]
api_hash = config["api_hash"]

bot = TelegramClient("pagermaid", api_key, api_hash)
bot.start()
