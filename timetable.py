import datetime
import hashlib
import locale

from config import SessionFactory, template_env

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


async def get_groups():
    async with SessionFactory() as session:
        response = await session.get('https://public.mai.ru/schedule/data/groups.json')
        response.raise_for_status()
    data = await response.json()
    return {gr["name"] for gr in data if "name" in gr}


async def get_group_data(group_name):
    group_md5 = hashlib.md5(group_name.encode()).hexdigest()
    async with SessionFactory() as session:
        response = await session.get(f'https://public.mai.ru/schedule/data/{group_md5}.json')
        response.raise_for_status()
    return await response.json()


def recode_str_date(x: str, *, src_format: str = '%y%W%u', dst_format: str = '%d.%m.%Y') -> str:
    return datetime.date.strftime(
        datetime.datetime.strptime(x, src_format), dst_format
    )


def repack_days_data(data: dict) -> dict:
    """This is really shit, thanks for the best API"""
    new_data = dict()
    for day, day_data in data.items():
        title = f"{recode_str_date(day, src_format='%d.%m.%Y', dst_format='%a')} ~ {day[:5]}"
        pairs = {}
        for start_time, pair in day_data.get('pairs', dict()).items():
            pair_title, value = next(iter(pair.items()), (None, None))
            if not value:
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

    if len(request) == 4:
        dates = [recode_str_date(f'{request}{weekday}') for weekday in range(1, 8)]
    elif len(request) == 5:
        dates = [recode_str_date(request)]
    else:
        raise ValueError(f"Malformed request: {request}")
    data = {date: data.get(date, dict()) for date in dates}

    template = template_env.get_template('timetable.html')
    return template.render(data=repack_days_data(data))
