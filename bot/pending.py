from dataclasses import dataclass


@dataclass
class PendingPost:
    """A collected carousel moving through the dialog: first awaiting the post
    text, then (if there is any text) awaiting the text position choice."""

    file_ids: list[str]
    caption: str | None = None
    body: str | None = None
    awaiting_position: bool = False


def merge_pending(
    pending: dict[int, PendingPost],
    chat_id: int,
    file_ids: list[str],
    caption: str | None,
) -> PendingPost:
    """Store a fresh collection, or extend one already in the dialog
    (photos sent mid-dialog join the same post and restart it at the
    text question)."""
    post = pending.get(chat_id)
    if post is None:
        post = PendingPost(list(file_ids), caption)
        pending[chat_id] = post
    else:
        post.file_ids.extend(file_ids)
        post.caption = caption or post.caption
        post.awaiting_position = False
    return post
