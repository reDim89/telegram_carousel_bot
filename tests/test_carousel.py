from bot.carousel import build_albums, post_message


def test_post_message_builds_slideshow_html_with_media_refs():
    msg = post_message(["f1", "f2", "f3"])
    assert msg.html == (
        "<tg-slideshow>"
        '<img src="tg://photo?id=p0"><img src="tg://photo?id=p1"><img src="tg://photo?id=p2">'
        "</tg-slideshow>"
    )
    assert [(m.id, m.media.media) for m in msg.media] == [
        ("p0", "f1"),
        ("p1", "f2"),
        ("p2", "f3"),
    ]


def test_post_message_title_and_caption_order():
    msg = post_message(["f1", "f2"], caption="cap", title="Summer 2026")
    assert msg.html.startswith("<h1>Summer 2026</h1><tg-slideshow>")
    assert msg.html.endswith("</tg-slideshow><p>cap</p>")


def test_post_message_passes_user_html_through_verbatim():
    caption = '<b>Wow</b> <a href="https://example.com">link</a>'
    title = '<i>Trip</i> <tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>'
    msg = post_message(["f1", "f2"], caption=caption, title=title)
    assert f"<h1>{title}</h1>" in msg.html
    assert f"<p>{caption}</p>" in msg.html


def test_post_message_single_photo_has_no_slideshow_tag():
    msg = post_message(["f1"], caption="cap", title="One shot")
    assert "<tg-slideshow>" not in msg.html
    assert msg.html == '<h1>One shot</h1><img src="tg://photo?id=p0"><p>cap</p>'
    assert [(m.id, m.media.media) for m in msg.media] == [("p0", "f1")]


def test_empty_input_builds_nothing():
    assert build_albums([]) == []


def test_single_photo_is_its_own_album():
    assert build_albums(["a"]) == [["a"]]


def test_up_to_ten_photos_fit_one_album():
    ids = [f"f{i}" for i in range(10)]
    assert build_albums(ids) == [ids]


def test_overflow_splits_into_balanced_albums():
    ids = [f"f{i}" for i in range(11)]
    albums = build_albums(ids)
    assert [len(a) for a in albums] == [6, 5]
    assert [fid for album in albums for fid in album] == ids  # order preserved


def test_large_batch_never_exceeds_album_limit():
    albums = build_albums([f"f{i}" for i in range(27)])
    assert [len(a) for a in albums] == [9, 9, 9]
    assert all(2 <= len(a) <= 10 for a in albums)
