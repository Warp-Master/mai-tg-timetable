import hashlib
from datetime import timedelta

from aiohttp_client_cache import CachedSession
from aiohttp_client_cache.backends import SQLiteBackend


CACHE = SQLiteBackend(
    cache_name='aiohttp-requests.db',
    expire_after=timedelta(hours=2),
    allowed_codes=(200,),
    allowed_methods=('GET',),
    timeout=2.5,
)

HEADERS = {'User-Agent': ''}


async def get_timetable(group):
    group_md5 = hashlib.md5(group.encode()).hexdigest()
    async with CachedSession(cache=CACHE, headers=HEADERS) as session:
        response = await session.get(f'https://public.mai.ru/schedule/data/{group_md5}.json')
        response.raise_for_status()
        data = await response.json()
    return str(data)[:256]


async def get_groups():
    async with CachedSession(cache=CACHE, headers=HEADERS) as session:
        response = await session.get('https://public.mai.ru/schedule/data/groups.json')
        response.raise_for_status()
        data = await response.json()
    return {gr.get("name") for gr in data}
