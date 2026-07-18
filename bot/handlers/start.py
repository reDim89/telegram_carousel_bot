from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

WELCOME = (
    "Send me several photos (as an album or one by one) and I'll turn them into "
    "a post with a swipable carousel — forward it anywhere, including channels.\n\n"
    "After the photos I'll ask for the post text (shown exactly as you wrote "
    "it, formatting included) and whether it goes above or below the photos. "
    "A caption on the photos works as post text too."
)


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME)
