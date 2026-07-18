import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto

from bot.carousel import build_albums, slideshow_message
from bot.collector import Collector
from bot.config import load_config
from bot.handlers import images, start

logger = logging.getLogger(__name__)


async def send_carousel(
    bot: Bot, chat_id: int, file_ids: list[str], caption: str | None = None
) -> None:
    if len(file_ids) == 1:
        await bot.send_photo(chat_id, file_ids[0], caption=caption)
        return
    try:
        await bot.send_rich_message(chat_id, rich_message=slideshow_message(file_ids, caption))
    except TelegramBadRequest as e:
        # Rich messages are new (Bot API 10.2); fall back to a classic album.
        logger.warning("Slideshow rejected (%s), falling back to media group", e)
        for album in build_albums(file_ids):
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

    async def flush(chat_id: int, file_ids: list[str], caption: str | None) -> None:
        await send_carousel(bot, chat_id, file_ids, caption)

    collector = Collector(flush)
    dp = Dispatcher(collector=collector)
    dp.include_routers(start.router, images.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
