from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

router = Router()

SKIP_CALLBACK = "skip_text"
POSITION_ABOVE = "pos:above"
POSITION_BELOW = "pos:below"
NO_PENDING = "Send me some photos first and I'll ask for the post text after."

# submit_text(chat_id, body|None) advances the dialog (asks for the text
# position, or publishes a textless post); returns False if nothing is pending.
SubmitTextCallback = Callable[[int, str | None], Awaitable[bool]]
# publish(chat_id, "above"|"below") sends the pending post; False if stale.
PublishCallback = Callable[[int, str], Awaitable[bool]]


@router.message(F.text, ~F.text.startswith("/"))
async def on_text(message: Message, submit_text: SubmitTextCallback) -> None:
    # html_text keeps the user's formatting entities.
    if not await submit_text(message.chat.id, message.html_text):
        await message.answer(NO_PENDING)


@router.callback_query(F.data == SKIP_CALLBACK)
async def on_skip(query: CallbackQuery, submit_text: SubmitTextCallback) -> None:
    await query.answer()
    advanced = await submit_text(query.message.chat.id, None)
    if advanced and query.message is not None:
        # Drop the Skip button so a second tap can't land on a stale prompt.
        await query.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.in_({POSITION_ABOVE, POSITION_BELOW}))
async def on_position(query: CallbackQuery, publish: PublishCallback) -> None:
    await query.answer()
    position = "above" if query.data == POSITION_ABOVE else "below"
    published = await publish(query.message.chat.id, position)
    if published and query.message is not None:
        await query.message.edit_reply_markup(reply_markup=None)
