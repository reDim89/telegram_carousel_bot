import math

from aiogram.types import InputMediaPhoto, InputRichMessage, InputRichMessageMedia

# Telegram media groups hold 2-10 items; a chunk of 1 must be sent as a plain photo.
ALBUM_LIMIT = 10


def post_message(
    file_ids: list[str], caption: str | None = None, title: str | None = None
) -> InputRichMessage:
    """Rich message (Bot API 10.2+) shaped like a post: optional <h1> title,
    a <tg-slideshow> (native swipable carousel with dots), optional <p> caption
    below. Authored as HTML so `caption` and `title` — Telegram-HTML strings
    taken verbatim from Message.html_text — keep the user's formatting exactly
    (bold, links, spoilers, custom emoji, ...). Photos are referenced via
    tg://photo?id= links resolved by the `media` list.
    """
    images = "".join(f'<img src="tg://photo?id=p{i}">' for i in range(len(file_ids)))
    parts = []
    if title:
        parts.append(f"<h1>{title}</h1>")
    if len(file_ids) == 1:
        parts.append(images)
    else:
        parts.append(f"<tg-slideshow>{images}</tg-slideshow>")
    if caption:
        parts.append(f"<p>{caption}</p>")
    return InputRichMessage(
        html="".join(parts),
        media=[
            InputRichMessageMedia(id=f"p{i}", media=InputMediaPhoto(media=file_id))
            for i, file_id in enumerate(file_ids)
        ],
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
