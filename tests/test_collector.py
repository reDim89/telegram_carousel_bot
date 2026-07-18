import asyncio

from bot.collector import Collector

Flush = tuple[int, list[str], str | None]


def make_collector(flushes: list[Flush], delay: float = 0.05) -> Collector:
    async def flush(chat_id: int, file_ids: list[str], caption: str | None) -> None:
        flushes.append((chat_id, file_ids, caption))

    return Collector(flush, delay=delay)


async def test_debounce_aggregates_album_into_one_flush():
    flushes: list[Flush] = []
    collector = make_collector(flushes)
    collector.add(1, "a")
    collector.add(1, "b")
    collector.add(1, "c")
    await asyncio.sleep(0.15)

    assert flushes == [(1, ["a", "b", "c"], None)]


async def test_chats_are_isolated():
    flushes: list[Flush] = []
    collector = make_collector(flushes)
    collector.add(1, "a")
    collector.add(2, "b")
    await asyncio.sleep(0.15)

    assert sorted(flushes) == [(1, ["a"], None), (2, ["b"], None)]


async def test_new_photo_resets_the_timer():
    flushes: list[Flush] = []
    collector = make_collector(flushes, delay=0.1)
    collector.add(1, "a")
    await asyncio.sleep(0.06)  # still within the quiet period
    collector.add(1, "b")
    await asyncio.sleep(0.06)  # first timer would have fired by now if not reset
    assert flushes == []
    await asyncio.sleep(0.1)
    assert flushes == [(1, ["a", "b"], None)]


async def test_caption_set_before_photos_is_used_and_cleared():
    flushes: list[Flush] = []
    collector = make_collector(flushes)

    assert collector.set_caption(1, "My trip") is False  # nothing buffered yet
    collector.add(1, "a")
    collector.add(1, "b")
    await asyncio.sleep(0.15)
    assert flushes == [(1, ["a", "b"], "My trip")]

    collector.add(1, "c")
    await asyncio.sleep(0.15)
    assert flushes[1] == (1, ["c"], None)  # caption was consumed


async def test_caption_during_collection_extends_the_window():
    flushes: list[Flush] = []
    collector = make_collector(flushes, delay=0.1)
    collector.add(1, "a")
    await asyncio.sleep(0.06)
    assert collector.set_caption(1, "text") is True  # photos pending
    await asyncio.sleep(0.06)  # original timer would have fired; caption re-armed it
    assert flushes == []
    await asyncio.sleep(0.1)
    assert flushes == [(1, ["a"], "text")]


async def test_caption_is_per_chat():
    flushes: list[Flush] = []
    collector = make_collector(flushes)
    collector.set_caption(1, "for chat one")
    collector.add(2, "b")
    await asyncio.sleep(0.15)
    assert flushes == [(2, ["b"], None)]
