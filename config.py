from datetime import timedelta
from functools import partial

from aiohttp_client_cache import CachedSession
from aiohttp_client_cache.backends import SQLiteBackend
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

load_dotenv()


CACHE = SQLiteBackend(
    cache_name='aiohttp-requests.db',
    expire_after=timedelta(hours=2),
    allowed_codes=(200,),
    allowed_methods=('GET',),
    timeout=2.5,
)

HEADERS = {'User-Agent': ''}

SessionFactory = partial(CachedSession, cache=CACHE, headers=HEADERS)


template_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    # trim_blocks=True,
    # lstrip_blocks=True
)
