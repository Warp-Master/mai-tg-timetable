import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram.types import Update

from config import redis_client
import redis
import logging


background_tasks = set()


async def add_to_uniq_users(user_id):
    try:
        await redis_client.sadd('uniq_users', user_id)
    except redis.exceptions.ConnectionError:
        logging.error('Cant connect to redis')


async def statistics_middleware(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
) -> Any:
    res = await handler(event, data)
    user_id = data['event_from_user'].id
    task = asyncio.create_task(add_to_uniq_users(user_id))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return res
