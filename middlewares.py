import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram.types import Update

from config import redis_client


async def statistics_middleware(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
) -> Any:
    res = await handler(event, data)
    user_id = data['event_from_user'].id
    asyncio.ensure_future(redis_client.sadd('uniq_users', user_id))
    return res
