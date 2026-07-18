from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

WELCOME = (
    "Send me several photos (as an album or one by one) and I'll turn them into "
    "a post with a swipable carousel — forward it anywhere, including channels.\n\n"
    "Add a caption to the photos to get text below the carousel. After the photos "
    "I'll ask for a title, which you can skip."
)


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME)
