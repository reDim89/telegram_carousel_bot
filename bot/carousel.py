import math

from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockPhoto,
    InputRichBlockSlideshow,
    InputRichMessage,
    RichBlockCaption,
)

# Telegram media groups hold 2-10 items; a chunk of 1 must be sent as a plain photo.
ALBUM_LIMIT = 10


def slideshow_message(file_ids: list[str], caption: str | None = None) -> InputRichMessage:
    """Rich message (Bot API 10.2+) with one slideshow block — the native swipable
    carousel with dot indicators. The caption renders below the slideshow."""
    return InputRichMessage(
        blocks=[
            InputRichBlockSlideshow(
                blocks=[
                    InputRichBlockPhoto(photo=InputMediaPhoto(media=file_id))
                    for file_id in file_ids
                ],
                caption=RichBlockCaption(text=caption) if caption else None,
            )
        ]
    )


def build_albums(file_ids: list[str]) -> list[list[str]]:
    """Split photos into media-group-sized albums, preserving order.

    Chunks are balanced (11 photos -> 6+5, not 10+1) so an overflow never
    leaves a stray near-empty album.
    """
    n = len(file_ids)
    if n == 0:
        return []
    num_albums = math.ceil(n / ALBUM_LIMIT)
    base, extra = divmod(n, num_albums)
    albums = []
    start = 0
    for i in range(num_albums):
        size = base + (1 if i < extra else 0)
        albums.append(file_ids[start : start + size])
        start += size
    return albums
