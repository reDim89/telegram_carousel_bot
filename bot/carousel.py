import math

from aiogram.types import InputMediaPhoto, InputRichMessage, InputRichMessageMedia

# Telegram media groups hold 2-10 items; a chunk of 1 must be sent as a plain photo.
ALBUM_LIMIT = 10


def _text_block(text: str) -> str:
    # Raw newlines are just whitespace in HTML, so every newline becomes <br>.
    # Deliberately NOT split into <p> per blank line: clients render <p> gaps
    # smaller than a real empty line, so <br><br> is the faithful reproduction.
    return f"<p>{text.replace(chr(10), '<br>')}</p>"


def post_message(
    file_ids: list[str],
    caption: str | None = None,
    body: str | None = None,
    text_position: str = "above",
) -> InputRichMessage:
    """Rich message (Bot API 10.2+) shaped like a post: the text — body (typed
    after the photos) and/or caption (attached to the photos) — as a plain <p>
    block above or below (`text_position`) the <tg-slideshow> (native swipable
    carousel with dots). No headings: the user's text is never restyled.
    Authored as HTML so the Telegram-HTML strings taken verbatim from
    Message.html_text keep the user's formatting exactly (bold, links,
    spoilers, custom emoji, ...). Photos are referenced via tg://photo?id=
    links resolved by `media`.
    """
    images = "".join(f'<img src="tg://photo?id=p{i}">' for i in range(len(file_ids)))
    if len(file_ids) > 1:
        images = f"<tg-slideshow>{images}</tg-slideshow>"
    texts = [_text_block(t) for t in (body, caption) if t]
    if text_position == "below":
        parts = [images, *texts]
    else:
        parts = [*texts, images]
    return InputRichMessage(
        html="".join(parts),
        # The text carries the user's entities verbatim; auto-detection could
        # only add overlapping duplicates.
        skip_entity_detection=True,
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
