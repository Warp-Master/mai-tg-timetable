import asyncio
from datetime import datetime, timedelta
from os import getenv
from typing import Any, Awaitable, Callable, Dict

from aiogram.types import Update

from db import db

ACCESS_LOG_TTL = int(getenv("ACCESS_LOG_TTL"))


async def access_log_middleware(
    handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
    event: Update,
    data: Dict[str, Any]
) -> Any:
    loop = asyncio.get_running_loop()
    t_start = loop.time()
    res = await handler(event, data)
    t_stop = loop.time()

    utc_now = datetime.utcnow()
    data = {
        'ts': utc_now,
        'expireAt': utc_now + timedelta(days=ACCESS_LOG_TTL),
        'handler': data['handler'].callback.__name__,
        'user_id': data['event_from_user'].id,
        'duration': t_stop - t_start,
    }
    await db.access_log.insert_one(data)
    return res
