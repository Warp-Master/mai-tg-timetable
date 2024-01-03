import asyncio
import logging
import sys
from datetime import date
from difflib import get_close_matches

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hunderline

from config import TOKEN
from keyboards import get_confirm_markup, get_timetable_markup, TimetableRequest
from timetable import get_groups
from timetable import get_timetable_msg

dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Привет, {hbold(message.from_user.full_name)}!\n"
                         "Напишите свою группу\n"
                         f"Пример: {hbold('М6О-208Б-22')}")


@dp.message()
async def process_group(message: Message) -> None:
    group = message.text
    all_groups = await get_groups()

    if group in all_groups:
        await timetable_handler(message, TimetableRequest(group=group, body='week'))
    else:
        possible_group = get_close_matches(group, all_groups, n=1, cutoff=0.0)[0]
        await message.answer(
            f"Может быть {hunderline(possible_group)}?",
            reply_markup=get_confirm_markup(possible_group)
        )


@dp.callback_query(F.data == "hide")
async def hide_callback_query(query: CallbackQuery) -> None:
    await query.message.delete()


async def timetable_handler(obj: Message | CallbackQuery, callback_data):
    if isinstance(obj, CallbackQuery):
        message = obj.message
    elif isinstance(obj, Message):
        message = obj
    else:
        raise ValueError("First argument must be instance of Message or CallbackQuery")

    group, request = callback_data.group, callback_data.body
    if request == 'day':
        request = date.today().strftime('%y%W%u')
    elif request == 'week':
        request = date.today().strftime('%y%W')

    if message.from_user.id == bot.id:
        action = message.edit_text
    else:
        action = message.answer
    await action(text=await get_timetable_msg(group, request),
                 reply_markup=get_timetable_markup(group, request),
                 parse_mode=ParseMode.HTML)


dp.callback_query(TimetableRequest.filter())(timetable_handler)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
