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


@dp.message(F.text)
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
    group, request = callback_data.group, callback_data.body
    today = date.today()

    if isinstance(obj, CallbackQuery):
        message = obj.message
        action = message.edit_text

        if request == 'day' and callback_data.showing == today.strftime('%y%W%u'):
            return await obj.answer('Уже на текущем дне')
        if request == 'week' and callback_data.showing == today.strftime('%y%W'):
            return await obj.answer('Уже на текущей неделе')
    elif isinstance(obj, Message):
        action = obj.answer
    else:
        raise ValueError("First argument must be instance of Message or CallbackQuery")

    if request == 'day':
        request = today.strftime('%y%W%u')
    elif request == 'week':
        request = today.strftime('%y%W')

    return await action(text=await get_timetable_msg(group, request),
                        reply_markup=get_timetable_markup(group, request))


dp.callback_query(TimetableRequest.filter())(timetable_handler)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
