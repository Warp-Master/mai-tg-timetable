from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class GroupCallback(CallbackData, prefix='gr'):
    name: str
    week: int | None = None
    day: int | None = None


def get_confirm_markup(group: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Нет", callback_data="hide"),
            InlineKeyboardButton(text="Да", callback_data=GroupCallback(name=group).pack())
        ]]
    )
