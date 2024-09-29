import locale
from datetime import date, datetime
from typing import Any

from aiogram.utils.formatting import BlockQuote, Bold, Text

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


def request_processor(request: str) -> str:
    today = date.today()
    if request == "day":
        return today.strftime("%y%W%u")
    elif request == "week":
        return today.strftime("%y%W")
    else:
        return request


async def get_timetable_msg(api, group, request):
    data = await api.get_group_data(group)
    if len(request) == 4:
        dates = [
            datetime.strptime(f"{request}{weekday}", "%y%W%u").date()
            for weekday in range(1, 8)
        ]
    elif len(request) == 5:
        dates = [datetime.strptime(request, "%y%W%u").date()]
    else:
        raise ValueError(f"Malformed request: {request}")

    # \n needed after each quote for prevent quote join on mac / ios clients
    # HTML / Markdown parsers can't create such messages
    parts: Any = [BlockQuote(Bold(group))]
    for d in dates:
        day = data[d]
        day_parts: Any = [Bold(day["title"])]
        if not day.get("pairs"):
            parts += ["\n", BlockQuote(*day_parts, "\nВыходной")]
            continue
        is_first_pair = True
        for pair in day.get("pairs", {}).values():
            day_parts += [
                "\n" if is_first_pair else "\n\n",
                f"{pair.get("title", "")}\n",
                f"{pair["lector"]}\n" if pair.get("lector") else "",
                f"{pair.get("time_start", "")}-{pair.get("time_end", "")}   {pair.get("type", "")}   {pair.get("room", "")}",
            ]
            is_first_pair = False
        parts += [
            "\n",
            BlockQuote(*day_parts),
        ]

    message = Text(*parts)

    return message
