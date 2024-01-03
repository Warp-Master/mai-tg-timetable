from datetime import timedelta
from os import getenv

from aiohttp_client_cache import CachedSession
from aiohttp_client_cache.backends import SQLiteBackend
from dotenv import load_dotenv
from functools import partial

load_dotenv()
TOKEN = getenv("BOT_TOKEN")


CACHE = SQLiteBackend(
    cache_name='aiohttp-requests.db',
    expire_after=timedelta(hours=2),
    allowed_codes=(200,),
    allowed_methods=('GET',),
    timeout=2.5,
)

HEADERS = {'User-Agent': ''}

SessionFactory = partial(CachedSession, cache=CACHE, headers=HEADERS)
