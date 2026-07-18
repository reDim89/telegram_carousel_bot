from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

WELCOME = (
    "Send me several photos (as an album or one by one) and I'll turn them into "
    "a post with a swipable carousel — forward it anywhere, including channels.\n\n"
    "Your text goes above the carousel, exactly as you wrote it: either add a "
    "caption to the photos, or send the text when I ask after the photos."
)


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME)
