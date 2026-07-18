from aiogram import F, Router
from aiogram.types import Message

from bot.collector import Collector

router = Router()


@router.message(F.photo)
async def on_photo(message: Message, collector: Collector) -> None:
    # An album caption arrives attached to one of the album's photos; it becomes
    # the text below the carousel.
    if message.caption:
        collector.set_caption(message.chat.id, message.caption)
    # message.photo lists size variants of one photo; [-1] is the largest.
    collector.add(message.chat.id, message.photo[-1].file_id)
