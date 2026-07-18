from dataclasses import dataclass


@dataclass
class PendingPost:
    """A collected carousel waiting for the user to provide/skip a title."""

    file_ids: list[str]
    caption: str | None = None


def merge_pending(
    pending: dict[int, PendingPost],
    chat_id: int,
    file_ids: list[str],
    caption: str | None,
) -> PendingPost:
    """Store a fresh collection, or extend one already awaiting a title
    (photos sent while the title question is open join the same post)."""
    post = pending.get(chat_id)
    if post is None:
        post = PendingPost(list(file_ids), caption)
        pending[chat_id] = post
    else:
        post.file_ids.extend(file_ids)
        post.caption = caption or post.caption
    return post
