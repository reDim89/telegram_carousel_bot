from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

router = Router()

SKIP_CALLBACK = "skip_title"
NO_PENDING = "Send me some photos first and I'll ask for the title after."

# publish(chat_id, title) sends the pending post; returns False if none pending.
PublishCallback = Callable[[int, str | None], Awaitable[bool]]


@router.message(F.text, ~F.text.startswith("/"))
async def on_title(message: Message, publish: PublishCallback) -> None:
    if not await publish(message.chat.id, message.text):
        await message.answer(NO_PENDING)


@router.callback_query(F.data == SKIP_CALLBACK)
async def on_skip(query: CallbackQuery, publish: PublishCallback) -> None:
    await query.answer()
    published = await publish(query.message.chat.id, None)
    if published and query.message is not None:
        # Drop the Skip button so a second tap can't land on a stale prompt.
        await query.message.edit_reply_markup(reply_markup=None)
