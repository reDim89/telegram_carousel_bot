from aiogram import F, Router
from aiogram.types import Message

from bot.collector import Collector

router = Router()

CAPTION_SAVED = "✍️ Saved — this text will appear under your next carousel."


@router.message(F.photo)
async def on_photo(message: Message, collector: Collector) -> None:
    # An album caption arrives attached to one of the album's photos.
    if message.caption:
        collector.set_caption(message.chat.id, message.caption)
    # message.photo lists size variants of one photo; [-1] is the largest.
    collector.add(message.chat.id, message.photo[-1].file_id)


@router.message(F.text, ~F.text.startswith("/"))
async def on_text(message: Message, collector: Collector) -> None:
    flushing_soon = collector.set_caption(message.chat.id, message.text)
    if not flushing_soon:
        await message.answer(CAPTION_SAVED)
