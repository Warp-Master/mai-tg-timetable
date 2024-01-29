import locale
from datetime import date, datetime

from config import template_env

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


def request_processor(request: str) -> str:
    today = date.today()
    if request == 'day':
        return today.strftime('%y%W%u')
    elif request == 'week':
        return today.strftime('%y%W')
    else:
        return request


async def get_timetable_msg(api, group, request):
    data = await api.get_group_data(group)
    if len(request) == 4:
        dates = [datetime.strptime(f'{request}{weekday}', '%y%W%u').date() for weekday in range(1, 8)]
    elif len(request) == 5:
        dates = [datetime.strptime(request, '%y%W%u').date()]
    else:
        raise ValueError(f'Malformed request: {request}')
    data = [data[d] for d in dates]

    template = template_env.get_template('timetable.html')
    return template.render(title=group, data=data)
