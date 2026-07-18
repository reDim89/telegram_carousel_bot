import asyncio
from collections.abc import Awaitable, Callable

FlushCallback = Callable[[int, list[str], str | None], Awaitable[None]]

DEFAULT_DELAY = 2.0


class Collector:
    """Buffers incoming photo file_ids (and an optional caption) per chat and
    flushes after a quiet period.

    Telegram delivers album photos as separate updates with no end-of-album
    signal, so each photo (re)arms a per-chat timer and the buffer is flushed
    once no new photo has arrived for `delay` seconds. A caption set with no
    photos buffered is kept until the next flush for that chat.
    """

    def __init__(self, flush: FlushCallback, delay: float = DEFAULT_DELAY):
        self._flush = flush
        self._delay = delay
        self._buffers: dict[int, list[str]] = {}
        self._captions: dict[int, str] = {}
        self._timers: dict[int, asyncio.Task] = {}

    def add(self, chat_id: int, file_id: str) -> None:
        self._buffers.setdefault(chat_id, []).append(file_id)
        self._arm_timer(chat_id)

    def set_caption(self, chat_id: int, text: str) -> bool:
        """Remember the caption for the chat's next carousel.

        Returns True if photos are already buffered (the carousel is about to
        flush with this caption), False if the caption is stored for later.
        """
        self._captions[chat_id] = text
        if chat_id in self._buffers:
            # Give the user the full quiet period again after typing.
            self._arm_timer(chat_id)
            return True
        return False

    def _arm_timer(self, chat_id: int) -> None:
        timer = self._timers.get(chat_id)
        if timer is not None:
            timer.cancel()
        self._timers[chat_id] = asyncio.create_task(self._fire(chat_id))

    async def _fire(self, chat_id: int) -> None:
        await asyncio.sleep(self._delay)
        self._timers.pop(chat_id, None)
        file_ids = self._buffers.pop(chat_id, [])
        if file_ids:
            caption = self._captions.pop(chat_id, None)
            await self._flush(chat_id, file_ids, caption)
