import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from bot.carousel import build_albums, post_message
from bot.collector import Collector
from bot.config import load_config
from bot.handlers import images, start, title
from bot.pending import PendingPost, merge_pending

logger = logging.getLogger(__name__)

ASK_TEXT = "📝 Send the post text, or skip it."
ASK_POSITION = "📍 Where should the text go?"

TEXT_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Skip", callback_data=title.SKIP_CALLBACK)]]
)
POSITION_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬆️ Above the photos", callback_data=title.POSITION_ABOVE),
            InlineKeyboardButton(text="⬇️ Below the photos", callback_data=title.POSITION_BELOW),
        ]
    ]
)


async def send_post(bot: Bot, chat_id: int, post: PendingPost, position: str) -> None:
    # post.caption and post.body are Telegram-HTML (from Message.html_text),
    # so every plain-send path below must use parse_mode="HTML".
    if len(post.file_ids) == 1 and not post.body and not post.caption:
        await bot.send_photo(chat_id, post.file_ids[0])
        return
    try:
        await bot.send_rich_message(
            chat_id,
            rich_message=post_message(post.file_ids, post.caption, post.body, position),
        )
    except TelegramBadRequest as e:
        # Rich messages are new (Bot API 10.2); fall back to a classic album with
        # the text folded into the caption (always below - albums have no choice).
        logger.warning("Rich post rejected (%s), falling back to media group", e)
        caption = "\n\n".join(filter(None, [post.body, post.caption])) or None
        for album in build_albums(post.file_ids):
            if len(album) == 1:
                await bot.send_photo(chat_id, album[0], caption=caption, parse_mode="HTML")
            else:
                # A single captioned item shows the text below the whole album.
                media = [
                    InputMediaPhoto(
                        media=file_id,
                        caption=caption if i == 0 else None,
                        parse_mode="HTML" if i == 0 else None,
                    )
                    for i, file_id in enumerate(album)
                ]
                await bot.send_media_group(chat_id, media)
            caption = None  # only under the first album of an overflow batch


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    config = load_config()
    bot = Bot(config.bot_token)
    pending: dict[int, PendingPost] = {}

    async def flush(chat_id: int, file_ids: list[str], caption: str | None) -> None:
        merge_pending(pending, chat_id, file_ids, caption)
        await bot.send_message(chat_id, ASK_TEXT, reply_markup=TEXT_KEYBOARD)

    async def submit_text(chat_id: int, body: str | None) -> bool:
        post = pending.get(chat_id)
        if post is None:
            return False
        post.body = body
        if post.body or post.caption:
            post.awaiting_position = True
            await bot.send_message(chat_id, ASK_POSITION, reply_markup=POSITION_KEYBOARD)
        else:
            # Nothing to position - publish right away.
            pending.pop(chat_id)
            await send_post(bot, chat_id, post, position="above")
        return True

    async def publish(chat_id: int, position: str) -> bool:
        post = pending.get(chat_id)
        if post is None or not post.awaiting_position:
            return False
        pending.pop(chat_id)
        await send_post(bot, chat_id, post, position)
        return True

    collector = Collector(flush)
    dp = Dispatcher(collector=collector, submit_text=submit_text, publish=publish)
    dp.include_routers(start.router, images.router, title.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
