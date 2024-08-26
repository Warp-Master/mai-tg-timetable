from os import environ, getenv

from aiogram.types import BotCommand
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

import redis.asyncio as redis

load_dotenv()

try:
    BOT_TOKEN = environ["BOT_TOKEN"]

    GROUP_LIST_CACHE_TTL = int(environ["GROUP_LIST_CACHE_TTL"])
    GROUP_DATA_CACHE_TTL = int(environ["GROUP_DATA_CACHE_TTL"])

    USE_LONG_POLLING = getenv("USE_LONG_POLLING")
    if not USE_LONG_POLLING:
        WEB_SERVER_PORT = int(getenv("WEB_SERVER_PORT", 8080))
        WEBHOOK_PATH = environ["WEBHOOK_PATH"]
        WEBHOOK_SECRET = environ["WEBHOOK_SECRET"]
        BASE_WEBHOOK_URL = environ["BASE_WEBHOOK_URL"]
    else:
        WEB_SERVER_PORT = None
        WEBHOOK_PATH = ""
        WEBHOOK_SECRET = None
        BASE_WEBHOOK_URL = None

    REDIS_URL = environ["REDIS_URL"]
except KeyError as e:
    raise EnvironmentError(f"Check your environment file (.env) for key {e.args[0]}")

template_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    # trim_blocks=True,
    # lstrip_blocks=True
)

bot_commands = [
    BotCommand(command="help", description="Справка"),
    BotCommand(command="about", description="Репозиторий проекта и мои контакты"),
    BotCommand(command="plan", description="План-схема кампуса МАИ"),
    BotCommand(
        command="bigplan", description="Подробная план-схема кампуса МАИ (файл)"
    ),
    BotCommand(command="stats", description="Статистика"),
]

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
redis_ts = redis_client.ts()
