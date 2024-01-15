from functools import partial

from aiohttp import ClientSession
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

load_dotenv()

HEADERS = {'User-Agent': ''}

SessionFactory = partial(ClientSession, headers=HEADERS)


template_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    # trim_blocks=True,
    # lstrip_blocks=True
)
