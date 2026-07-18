from bot.pending import PendingPost, merge_pending


def test_new_collection_creates_pending_post():
    pending: dict[int, PendingPost] = {}
    post = merge_pending(pending, 1, ["a", "b"], "cap")
    assert pending[1] is post
    assert post.file_ids == ["a", "b"]
    assert post.caption == "cap"


def test_photos_sent_while_title_pending_join_the_post():
    pending: dict[int, PendingPost] = {}
    merge_pending(pending, 1, ["a"], "first caption")
    post = merge_pending(pending, 1, ["b", "c"], None)
    assert post.file_ids == ["a", "b", "c"]
    assert post.caption == "first caption"  # kept when the new batch has none


def test_later_caption_wins():
    pending: dict[int, PendingPost] = {}
    merge_pending(pending, 1, ["a"], "old")
    post = merge_pending(pending, 1, ["b"], "new")
    assert post.caption == "new"
