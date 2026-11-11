# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Telegram bot that accepts a set of images from a user and turns them into a swipable carousel. Source lives on GitHub; CI runs on GitHub Actions; a self-hosted Linux machine deploys itself by pulling `master`.

## Stack

- Python 3.12+, **aiogram 3** (async), managed with **uv** (`pyproject.toml` + `uv.lock`)
- Lint/format: **ruff**; tests: **pytest** (+ pytest-asyncio)
- Runs in production as a systemd user service via `uv` (units and scripts in `deploy/`); the Dockerfile/compose file are only for running it containerized locally

## Commands

```bash
uv sync                          # install deps (incl. dev group)
uv run python -m bot             # run the bot locally (long polling; needs BOT_TOKEN)
uv run pytest                    # run all tests
uv run pytest tests/test_carousel.py::test_name   # run a single test
uv run ruff check . && uv run ruff format --check .   # lint (CI runs this)
docker compose up --build        # run the containerized bot locally
```

Configuration comes from environment variables (locally via `.env`, not committed): `BOT_TOKEN` is required.

## Architecture

The carousel is a native Telegram **slideshow**: a rich message (`sendRichMessage`, Bot API 10.2, July 2026 — needs aiogram ≥ 3.30) containing one `InputRichBlockSlideshow` of photo blocks referencing cached `file_id`s (never re-uploading). Clients render it with dot indicators on the image and in-place swiping, and it stays swipable when forwarded to channels. The bot is stateless — no store. Do not reintroduce the two approaches this replaced: inline-keyboard paging (`editMessageMedia` + callbacks) and plain `sendMediaGroup` albums (grid rendering); the latter survives only as the fallback when `sendRichMessage` is rejected.

The flow:

1. **Collection** — users send images either one-by-one or as an album. Album messages arrive as *separate* updates sharing a `media_group_id`, and Telegram sends no "album complete" signal — `collector.py` therefore aggregates incoming photos per chat with a short debounce before flushing. The caption (rendered below the carousel) comes *only* from the photo/album caption (`message.caption` on one of the album's photos).
2. **Dialog steps** — the collector flush does not publish; it stores a `PendingPost` (`pending.py`, in-memory per-chat dict) and asks for the post text (inline Skip button). The next plain text message is the post body (routed by `handlers/title.py` — this is why free text is *not* a caption). Then, if the post has any text (body or caption), the bot asks where it goes — ⬆️ above / ⬇️ below buttons — and publishes on that choice; with no text it publishes immediately after Skip. Photos sent mid-dialog merge into the same pending post and restart it at the text question. Dialog orchestration (`submit_text`/`publish` callbacks) lives in `__main__.py` closures.
3. **Rendering** — `send_post` sends one rich message built by `carousel.py:post_message` as **HTML** (`InputRichMessage.html` + `media` list; photos referenced by `tg://photo?id=` links): the text (body and/or photo caption) as plain `<p>` blocks above or below the `<tg-slideshow>` of `<img>`s per the user's position choice. **No headings** — `<h1>` restyles the user's text into large serif type, which was explicitly rejected; raw newlines are whitespace in HTML, so every `\n` → `<br>` within a single `<p>` (`_text_block`) — do *not* split blank lines into separate `<p>` blocks, clients render `<p>` gaps smaller than a real empty line. HTML (not blocks) is deliberate: text is captured with `Message.html_text`, which preserves the user's formatting entities (bold, links, spoilers, custom emoji) verbatim — **every string in `PendingPost` is Telegram-HTML, so any plain send path must pass `parse_mode="HTML"`** — and `skip_entity_detection=True` prevents Telegram from layering auto-detected entities on top. On `TelegramBadRequest` it falls back to classic albums with body+caption joined as the album caption: media groups hold 2–10 items, so `carousel.py:build_albums` splits N photos into balanced chunks (11 → 6+5, never 10+1); a chunk of exactly 1 must go via `send_photo`, not `send_media_group`.

The bot uses **long polling**, not webhooks — no public HTTPS endpoint, domain, or open port needed on the host.

Layout: `bot/` package — `__main__.py` (wiring, `send_post`, polling entrypoint), `collector.py` (debounced photo aggregation), `pending.py` (posts awaiting a title), `carousel.py` (pure message/album building), `handlers/` (thin aiogram routers; `collector` and the `publish` callback are injected via `Dispatcher(...)` kwargs). `tests/` covers collector, pending, and message-building logic without a live bot — keep it that way.

## CI/CD

- **PRs / pushes** (GitHub Actions, `ci.yml`): ruff + pytest.
- **Deploy** is pull-based, with no Actions job: on the host, `telegram-carousel-bot-update.timer` runs `deploy/update.sh` every ~2 minutes, which fast-forwards the deploy checkout (`~/services/telegram_carousel_bot`) to `origin/master`, runs `uv sync --frozen --no-dev`, and restarts `telegram-carousel-bot.service`. So anything pushed to `master` is live within minutes, whether or not CI passed.
- `deploy/install.sh` copies the units and update script out of the repo; changes under `deploy/` take effect only after re-running it on the host.
- `BOT_TOKEN` lives only on the host in the deploy checkout's `.env`, never in the repo or workflow files. There are no deploy secrets in GitHub.
