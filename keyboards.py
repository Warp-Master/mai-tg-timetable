from datetime import datetime, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class TimetableRequest(CallbackData, prefix='tt'):
    group: str
    # body may be %y%W (for week display) or %y%W%u (for day display)
    # also "week" means current week and "day" means current day
    body: str
    showing: str | None = None  # when body equals "week" or "day" stores current page


def get_confirm_markup(group: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Нет", callback_data="hide"),
            InlineKeyboardButton(text="Да", callback_data=TimetableRequest(group=group, body='week').pack())
        ]]
    )


def get_timetable_markup(group: str, request: str) -> InlineKeyboardMarkup:
    one_day = timedelta(days=1)

    current_day_request = TimetableRequest(group=group, body='day', showing=request).pack()
    current_week_request = TimetableRequest(group=group, body='week', showing=request).pack()

    if len(request) == 4:
        prev_page = (datetime.strptime(f'{request}1', '%y%W%u') - one_day).strftime('%y%W')
        next_page = (datetime.strptime(f'{request}7', '%y%W%u') + one_day).strftime('%y%W')
        home_callback = current_week_request
        switch_type = InlineKeyboardButton(text='По дням', callback_data=current_day_request)
    elif len(request) == 5:
        t = datetime.strptime(request, '%y%W%u')
        prev_page = (t - one_day).strftime('%y%W%u')
        next_page = (t + one_day).strftime('%y%W%u')
        home_callback = current_day_request
        switch_type = InlineKeyboardButton(text='По неделям', callback_data=current_week_request)
    else:
        raise ValueError(f"Malformed request {request}")
    prev_page = TimetableRequest(group=group, body=prev_page).pack()
    next_page = TimetableRequest(group=group, body=next_page).pack()

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="\u25C0", callback_data=prev_page),
                          InlineKeyboardButton(text='\U0001F3E0', callback_data=home_callback),
                          InlineKeyboardButton(text="\u25B6", callback_data=next_page)],
                         [switch_type]]
    )
