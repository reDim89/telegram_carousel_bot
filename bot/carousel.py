import math

from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockSlideshow,
    InputRichMessage,
    RichBlockCaption,
)

# Telegram media groups hold 2-10 items; a chunk of 1 must be sent as a plain photo.
ALBUM_LIMIT = 10


def post_message(
    file_ids: list[str], caption: str | None = None, title: str | None = None
) -> InputRichMessage:
    """Rich message (Bot API 10.2+) shaped like a post: optional heading on top,
    a slideshow (native swipable carousel with dots), caption below it. A single
    photo becomes a plain photo block instead of a slideshow."""
    block_caption = RichBlockCaption(text=caption) if caption else None
    if len(file_ids) == 1:
        media_block = InputRichBlockPhoto(
            photo=InputMediaPhoto(media=file_ids[0]), caption=block_caption
        )
    else:
        media_block = InputRichBlockSlideshow(
            blocks=[
                InputRichBlockPhoto(photo=InputMediaPhoto(media=file_id)) for file_id in file_ids
            ],
            caption=block_caption,
        )
    blocks = [media_block]
    if title:
        blocks.insert(0, InputRichBlockSectionHeading(text=title, size=1))
    return InputRichMessage(blocks=blocks)


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
