from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

WELCOME = (
    "Send me several photos (as an album or one by one) and I'll turn them into "
    "a swipable carousel with dots — forward it anywhere, including channels.\n\n"
    "To add text below the carousel, type a caption when sending the album, or "
    "send me the text as a message before the photos."
)


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME)
