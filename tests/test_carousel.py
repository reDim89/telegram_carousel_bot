from bot.carousel import build_albums, post_message


def test_post_message_wraps_photos_in_one_slideshow_block():
    msg = post_message(["f1", "f2", "f3"])
    [slideshow] = msg.blocks
    assert slideshow.type == "slideshow"
    assert [b.photo.media for b in slideshow.blocks] == ["f1", "f2", "f3"]
    assert all(b.type == "photo" for b in slideshow.blocks)
    assert slideshow.caption is None


def test_post_message_attaches_caption_to_slideshow():
    msg = post_message(["f1", "f2"], caption="My trip")
    [slideshow] = msg.blocks
    assert slideshow.caption.text == "My trip"


def test_post_message_puts_title_heading_above_slideshow():
    msg = post_message(["f1", "f2"], caption="cap", title="Summer 2026")
    heading, slideshow = msg.blocks
    assert heading.type == "heading"
    assert heading.text == "Summer 2026"
    assert slideshow.type == "slideshow"


def test_post_message_single_photo_uses_photo_block():
    msg = post_message(["f1"], caption="cap", title="One shot")
    heading, photo = msg.blocks
    assert heading.type == "heading"
    assert photo.type == "photo"
    assert photo.photo.media == "f1"
    assert photo.caption.text == "cap"


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
