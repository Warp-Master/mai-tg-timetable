from datetime import date

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import Field


class TimetableRequest(CallbackData, prefix='tt'):
    group: str
    # body may be %y%W (for week display) or %y%W%u (for day display)
    body: str = Field(default_factory=lambda: date.today().strftime('%y%W'))


def get_confirm_markup(group: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Нет", callback_data="hide"),
            InlineKeyboardButton(text="Да", callback_data=TimetableRequest(group=group).pack())
        ]]
    )
