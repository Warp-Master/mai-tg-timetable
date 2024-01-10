import logging
import sys
from datetime import date
from difflib import get_close_matches
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.utils.markdown import hunderline
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import template_env
from keyboards import get_confirm_markup, get_timetable_markup, TimetableRequest
from timetable import get_groups
from timetable import get_timetable_msg

dp = Dispatcher()

TOKEN = getenv("BOT_TOKEN")
WEBHOOK_SECRET = getenv("WEBHOOK_SECRET")


@dp.message(Command('start', 'help'))
async def command_start_handler(message: Message) -> None:
    await message.answer(template_env.get_template('start.html').render())


@dp.message(Command('about', 'github', 'contacts'))
async def command_about_handler(message: Message) -> None:
    await message.answer(template_env.get_template('about.html').render(), disable_web_page_preview=True)


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


@dp.callback_query(TimetableRequest.filter())
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


@dp.startup()
async def on_startup(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command='help', description='Help message'),
        BotCommand(command='about', description='Project repo and my contacts'),
    ])
    if not getenv("USE_LONG_PULLING"):
        await bot.set_webhook(
            f'{getenv("BASE_WEBHOOK_URL")}{getenv("WEBHOOK_PATH")}',
            secret_token=WEBHOOK_SECRET,
        )


@dp.shutdown()
async def on_shutdown(bot: Bot) -> None:
    if not getenv("USE_LONG_PULLING"):
        await bot.delete_webhook()


def start_webapp(bot: Bot) -> None:
    app = web.Application()
    # Create an instance of request handler,
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=getenv("WEBHOOK_PATH"))
    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)
    # And finally start webserver
    web.run_app(app, host="0.0.0.0", port=8080)


def start_pulling(bot: Bot) -> None:
    import asyncio
    asyncio.run(dp.start_polling(bot))


def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    if getenv("USE_LONG_PULLING"):
        start_webapp(bot)
    else:
        start_pulling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
