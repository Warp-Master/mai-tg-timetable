import asyncio
from time import time
from os import getenv
from typing import Any, Awaitable, Callable, Dict

from aiogram.types import Update
from config import redis_ts, redis_client

ACCESS_LOG_TTL = int(getenv("ACCESS_LOG_TTL")) * 24 * 60 * 60 * 1000


async def statistics_middleware(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
) -> Any:
    res = await handler(event, data)
    ts = int(time() * 1000)
    user_id = data['event_from_user'].id
    asyncio.ensure_future(
        redis_ts.add('access_log', ts, user_id,
                     labels={'handler': data['handler'].callback.__name__},
                     retention_msecs=ACCESS_LOG_TTL)
    )
    asyncio.ensure_future(redis_client.sadd('uniq_users', user_id))
    return res
