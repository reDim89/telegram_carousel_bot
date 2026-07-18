# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Telegram bot that accepts a set of images from a user and turns them into a swipable carousel. Source lives on GitHub; CI/CD via GitHub Actions deploys to a single VM.

## Stack

- Python 3.12+, **aiogram 3** (async), managed with **uv** (`pyproject.toml` + `uv.lock`)
- Lint/format: **ruff**; tests: **pytest** (+ pytest-asyncio)
- Runs in Docker on the VM via docker compose; images published to GHCR

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
2. **Title step** — the collector flush does not publish; it stores a `PendingPost` (`pending.py`, in-memory per-chat dict) and asks for a post title (inline Skip button). The next plain text message is the title (routed by `handlers/title.py` — this is why free text is *not* a caption); Skip publishes without one. Photos sent while the question is open merge into the same pending post.
3. **Rendering** — `send_post` sends one rich message (built by `carousel.py:post_message`): optional heading block (title) above, slideshow with the caption below; a single photo uses a photo block instead of a slideshow. On `TelegramBadRequest` it falls back to classic albums with the title folded into the caption: media groups hold 2–10 items, so `carousel.py:build_albums` splits N photos into balanced chunks (11 → 6+5, never 10+1); a chunk of exactly 1 must go via `send_photo`, not `send_media_group`.

The bot uses **long polling**, not webhooks — no public HTTPS endpoint, domain, or open port needed on the VM.

Layout: `bot/` package — `__main__.py` (wiring, `send_post`, polling entrypoint), `collector.py` (debounced photo aggregation), `pending.py` (posts awaiting a title), `carousel.py` (pure message/album building), `handlers/` (thin aiogram routers; `collector` and the `publish` callback are injected via `Dispatcher(...)` kwargs). `tests/` covers collector, pending, and message-building logic without a live bot — keep it that way.

## CI/CD (GitHub Actions)

- **PRs / pushes**: ruff + pytest.
- **Push to master** (the default branch): build the Docker image, push to GHCR, then SSH to the VM and run `docker compose pull && docker compose up -d`.
- GitHub secrets hold the VM SSH key/host; `BOT_TOKEN` lives only on the VM in its `.env`, never in the repo or workflow files.
