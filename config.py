from os import getenv

from aiogram.types import BotCommand
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

import redis.asyncio as redis

load_dotenv()

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

redis_client = redis.from_url(getenv("REDIS_URL"), decode_responses=True)
redis_ts = redis_client.ts()
