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

ASK_TITLE = "📝 Send a title for your post, or skip it."

TITLE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Skip", callback_data=title.SKIP_CALLBACK)]]
)


async def send_post(bot: Bot, chat_id: int, post: PendingPost, post_title: str | None) -> None:
    if len(post.file_ids) == 1 and not post_title:
        await bot.send_photo(chat_id, post.file_ids[0], caption=post.caption)
        return
    try:
        await bot.send_rich_message(
            chat_id, rich_message=post_message(post.file_ids, post.caption, post_title)
        )
    except TelegramBadRequest as e:
        # Rich messages are new (Bot API 10.2); fall back to a classic album with
        # the title folded into the caption.
        logger.warning("Rich post rejected (%s), falling back to media group", e)
        caption = "\n\n".join(filter(None, [post_title, post.caption])) or None
        for album in build_albums(post.file_ids):
            if len(album) == 1:
                await bot.send_photo(chat_id, album[0], caption=caption)
            else:
                # A single captioned item shows the text below the whole album.
                media = [
                    InputMediaPhoto(media=file_id, caption=caption if i == 0 else None)
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
        await bot.send_message(chat_id, ASK_TITLE, reply_markup=TITLE_KEYBOARD)

    async def publish(chat_id: int, post_title: str | None) -> bool:
        post = pending.pop(chat_id, None)
        if post is None:
            return False
        await send_post(bot, chat_id, post, post_title)
        return True

    collector = Collector(flush)
    dp = Dispatcher(collector=collector, publish=publish)
    dp.include_routers(start.router, images.router, title.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
