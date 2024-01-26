import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from os import getenv
from typing import Any

from aiohttp import ClientSession, ClientTimeout


def repack_group_data(data: dict) -> dict:
    new_data = DateDefaultDict()
    data.pop('group', None)
    for day, day_data in data.items():
        day = datetime.strptime(day, '%d.%m.%Y').date()
        pairs = {}
        for start_time, pair in day_data.get('pairs', dict()).items():
            pair_title, value = next(iter(pair.items()), (None, {}))
            if not pair_title:
                continue
            pairs[start_time] = {'title': pair_title,
                                 'time_start': value.get('time_start', '')[:-3],
                                 'time_end': value.get('time_end', '')[:-3],
                                 'lector': next(iter(value.get('lector', dict()).values()), '').title(),
                                 'type': next(iter(value.get('type', dict()).keys()), ''),
                                 'room': next(iter(value.get('room', dict()).values()), '')}
        new_data[day]['pairs'] = pairs
    return new_data


class DateDefaultDict(defaultdict):
    def __missing__(self, key):
        ret = self[key] = {'title': f"{date.strftime(key, '%a')} ~ {date.strftime(key, '%d.%m')}"}
        return ret


@dataclass
class CacheEntry:
    data: Any
    last_check: float
    etag: str

    def is_valid(self, ttl) -> bool:
        return time.time() < self.last_check + ttl


class CachedAPIClient:
    __slots__ = ('_session', '_cache', 'base_url', 'default_headers')

    def __init__(self, base_url: str, default_headers: dict):
        self._session = None
        self._cache = dict()
        self.base_url = base_url
        self.default_headers = default_headers

    async def __aenter__(self):
        self._session = ClientSession(
            raise_for_status=True,
            timeout=ClientTimeout(total=20)
        )
        return self

    async def __aexit__(self, *err):
        await self._session.close()

    # Needed for supporting cleanup_ctx in aiohttp application
    async def __call__(self, *args, **kwargs):
        async with self:
            yield

    async def fetch_json(self, key: str, filename_builder, cache_ttl: float, processor=None):
        cache_entry = self._cache.get(key)
        headers = self.default_headers
        if cache_entry:
            if cache_entry.is_valid(cache_ttl):
                return cache_entry.data
            if etag := cache_entry.etag:
                headers |= {'If-None-Match': etag}

        async with self._session.get(f'{self.base_url}{filename_builder(key)}', headers=headers) as response:
            if response.status == 304:
                cache_entry.last_check = time.time()
                return cache_entry.data

            res = await response.json()
            res = processor(res)
            self._cache[key] = CacheEntry(
                data=res,
                last_check=time.time(),
                etag=response.headers.get('etag')
            )
            return res

    async def get_groups(self):
        return await self.fetch_json(key='groups',
                                     filename_builder=lambda key: f'{key}.json',
                                     cache_ttl=int(getenv('GROUP_LIST_CACHE_TTL')),
                                     processor=lambda data: {gr["name"] for gr in data if "name" in gr})

    async def get_group_data(self, group_name):
        return await self.fetch_json(key=group_name,
                                     filename_builder=lambda key: f'{hashlib.md5(key.encode()).hexdigest()}.json',
                                     cache_ttl=int(getenv('GROUP_DATA_CACHE_TTL')),
                                     processor=repack_group_data)
