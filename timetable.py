import datetime
import hashlib
import locale
from datetime import date
from os import getenv

from aiocache import cached

from config import SessionFactory, template_env

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


@cached(ttl=int(getenv('GROUP_LIST_CACHE_TTL')), key='groups')
async def get_groups():
    async with SessionFactory() as session:
        async with session.get('https://public.mai.ru/schedule/data/groups.json') as response:
            response.raise_for_status()
            data = await response.json()
    return {gr["name"] for gr in data if "name" in gr}


@cached(ttl=int(getenv('GROUP_DATA_CACHE_TTL')), key_builder=lambda func, group_name: group_name)
async def get_group_data(group_name):
    group_md5 = hashlib.md5(group_name.encode()).hexdigest()
    async with SessionFactory() as session:
        async with session.get(f'https://public.mai.ru/schedule/data/{group_md5}.json') as response:
            response.raise_for_status()
            data = await response.json()
            data.pop('group', None)
    return data


def recode_str_date(x: str, *, src_format: str = '%y%W%u', dst_format: str = '%d.%m.%Y') -> str:
    return datetime.date.strftime(
        datetime.datetime.strptime(x, src_format), dst_format
    )


def request_processor(request: str) -> str:
    today = date.today()
    if request == 'day':
        return today.strftime('%y%W%u')
    elif request == 'week':
        return today.strftime('%y%W')
    else:
        return request


def repack_days_data(data: dict) -> dict:
    new_data = dict()
    for day, day_data in data.items():
        title = f"{recode_str_date(day, src_format='%d.%m.%Y', dst_format='%a')} ~ {day[:5]}"
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
        new_data[title] = pairs
    return new_data


async def get_timetable_msg(group, request):
    data = await get_group_data(group)

    request = request_processor(request)

    if len(request) == 4:
        dates = [recode_str_date(f'{request}{weekday}') for weekday in range(1, 8)]
    elif len(request) == 5:
        dates = [recode_str_date(request)]
    else:
        raise ValueError(f"Malformed request: {request}")
    data = {d: data.get(d, dict()) for d in dates}

    template = template_env.get_template('timetable.html')
    return template.render(data=repack_days_data(data))
