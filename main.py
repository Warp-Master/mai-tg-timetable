import logging
import sys
from difflib import get_close_matches
from functools import partial
from os import getenv
from time import time

from aiogram import Bot, Dispatcher, F
from aiogram import flags
from aiogram.enums import ParseMode
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED
from aiogram.types import ChatMemberUpdated
from aiogram.types import FSInputFile
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.utils.markdown import hunderline, hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from redis.exceptions import ConnectionError

from api import CachedAPIClient
from config import template_env, redis_client
from keyboards import get_confirm_markup, get_timetable_markup, get_load_markup, TimetableRequest
from middlewares import statistics_middleware
from timetable import get_timetable_msg
from timetable import request_processor

dp = Dispatcher(disable_fsm=True)
BOT = Bot(getenv('BOT_TOKEN'), parse_mode=ParseMode.HTML)
API = CachedAPIClient(base_url='https://public.mai.ru/schedule/data/',
                      default_headers={'User-Agent': ''})

PLAN_FILE_ID = None
BIGPLAN_FILE_ID = None
ABOUT_MESSAGE = template_env.get_template('about.html').render()
WEBHOOK_SECRET = getenv('WEBHOOK_SECRET')
EPOCH_START_TIME = int(time())


@dp.message(Command('start', 'help'))
async def command_start_handler(message: Message) -> None:
    me = await BOT.me()
    await message.answer(template_env.get_template('start.html').render(username=me.username))


@dp.message(Command('about', 'github', 'contacts'))
async def command_about_handler(message: Message) -> None:
    await message.answer(ABOUT_MESSAGE, disable_web_page_preview=True)


@dp.message(Command('plan'))
@flags.chat_action('upload_photo')
async def command_plan_handler(message: Message) -> None:
    global PLAN_FILE_ID
    file = FSInputFile('images/plan.webp')
    result = await message.answer_photo(PLAN_FILE_ID or file)
    PLAN_FILE_ID = result.photo[-1].file_id


@dp.message(Command('bigplan'))
@flags.chat_action('upload_document')
async def command_bigplan_handler(message: Message) -> None:
    global BIGPLAN_FILE_ID
    file = FSInputFile('images/big-plan.png', filename='MAI-plan.png')
    result = await message.answer_document(BIGPLAN_FILE_ID or file)
    BIGPLAN_FILE_ID = result.document.file_id


@dp.message(Command('stats'))
async def command_stats_handler(message: Message) -> None:
    uptime = int(time() - EPOCH_START_TIME)
    minutes, seconds = divmod(uptime, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    msg_parts = []
    if days:
        msg_parts.append(f'{days} days')
    msg_parts.append(f'{hours:02d}:{minutes:02d}:{seconds:02d}')
    try:
        user_cnt = await redis_client.scard('uniq_users')
        msg_parts.append(f'{user_cnt} users')
    except ConnectionError:
        logging.error("Can't connect to redis")
    await message.answer(f"Up {', '.join(msg_parts)}")


@dp.message(F.text & ~F.via_bot)
async def process_group(message: Message) -> None:
    group = message.text
    all_groups = await API.get_groups()

    if group in all_groups:
        await timetable_handler(message, TimetableRequest(group=group, body='week'))
    else:
        possible_group = get_close_matches(group, all_groups, n=1, cutoff=0.0)[0]
        await message.answer(
            f'Может быть {hunderline(possible_group)}?',
            reply_markup=get_confirm_markup(possible_group)
        )


@dp.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    group = query.query
    all_groups = await API.get_groups()

    possible_groups = get_close_matches(group, all_groups, n=10, cutoff=0.0)
    results = []
    for gr in possible_groups:
        content = InputTextMessageContent(message_text=hbold(gr))
        results.append(InlineQueryResultArticle(
            id=gr,
            title=gr,
            input_message_content=content,
            reply_markup=get_load_markup(gr)
        ))
    await query.answer(results=results, cache_time=3600)


@dp.callback_query(F.data == 'hide')
async def hide_callback_query(query: CallbackQuery) -> None:
    await query.message.delete()


@dp.callback_query(TimetableRequest.filter())
async def timetable_handler(obj: Message | CallbackQuery | ChosenInlineResult, callback_data):
    group, request, showing = callback_data.group, request_processor(callback_data.body), callback_data.showing
    if showing == request:
        if len(request) == 5:
            return await obj.answer('Уже на текущем дне')
        else:
            return await obj.answer('Уже на текущей неделе')

    if isinstance(obj, Message):
        action = obj.answer
    elif hasattr(obj, 'message') and obj.message is not None:
        action = obj.message.edit_text
    elif hasattr(obj, 'inline_message_id') and obj.inline_message_id is not None:
        action = partial(obj.bot.edit_message_text, inline_message_id=obj.inline_message_id)
    else:
        raise ValueError('Wrong event type')

    return await action(text=await get_timetable_msg(API, group, request),
                        reply_markup=get_timetable_markup(group, request))


@dp.chosen_inline_result()
async def chosen_handler(chosen_result: ChosenInlineResult):
    await timetable_handler(chosen_result, TimetableRequest(group=chosen_result.result_id, body='week'))


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def block_handler(event: ChatMemberUpdated):
    try:
        await redis_client.srem('uniq_users', event.from_user.id)
    except ConnectionError:
        logging.error('Cant connect to redis')

dp.message.middleware(ChatActionMiddleware())

USED_EVENT_TYPES = dp.resolve_used_update_types()
EVENT_TYPES_STAT_FREE = ['inline_query', 'my_chat_member']
for event_type in USED_EVENT_TYPES:
    if event_type not in EVENT_TYPES_STAT_FREE:
        dp.observers[event_type].middleware(statistics_middleware)


@dp.startup()
async def on_startup(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command='help', description='Справка'),
        BotCommand(command='about', description='Репозиторий проекта и мои контакты'),
        BotCommand(command='plan', description='План-схема кампуса МАИ'),
        BotCommand(command='bigplan', description='Подробная план-схема кампуса МАИ (файл)'),
        BotCommand(command='stats', description='Статистика')
    ])
    if getenv('USE_LONG_PULLING'):
        await bot.delete_webhook(drop_pending_updates=True)
    else:
        await bot.set_webhook(
            f"{getenv('BASE_WEBHOOK_URL')}{getenv('WEBHOOK_PATH')}",
            secret_token=WEBHOOK_SECRET,
            allowed_updates=USED_EVENT_TYPES,
        )


@dp.shutdown()
async def on_shutdown(bot: Bot) -> None:
    if not getenv('USE_LONG_PULLING'):
        await bot.delete_webhook()


def run_webapp(bot: Bot) -> None:
    app = web.Application()
    # Create an instance of request handler,
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=getenv('WEBHOOK_PATH'))
    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)
    app.cleanup_ctx.append(API)
    # And finally start webserver
    web.run_app(app, host='0.0.0.0', port=8080)


async def run_pulling(bot: Bot) -> None:
    async with API:
        await dp.start_polling(bot, allowed_updates=USED_EVENT_TYPES)


def main() -> None:
    if getenv('USE_LONG_PULLING'):
        import asyncio
        asyncio.run(run_pulling(BOT))
    else:
        run_webapp(BOT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
