# Telegram Carousel Bot

Send the bot several photos (as an album or one by one) and it turns them into a
post with a native Telegram **slideshow** — dot indicators on the image, swipable in
place — that you can forward to channels. Built on rich messages (`sendRichMessage`,
Bot API 10.2, July 2026). The flow: photos in, then the bot asks for the post text (skippable; a caption on
the photo album works too), then where the text goes — above or below the photos.
Formatting — bold, italic, links, spoilers, custom emoji, line breaks — is
preserved exactly as sent.
Photos are re-emitted by cached `file_id`, so nothing is re-uploaded, and the bot
keeps no persistent state. If Telegram rejects the rich message, it falls back to a
classic album (`sendMediaGroup`) with the title folded into the caption.

## Run locally

```bash
cp .env.example .env   # put your @BotFather token in BOT_TOKEN
uv sync
uv run python -m bot
```

Or containerized: `docker compose up --build`.

## Develop

```bash
uv run pytest                     # tests
uv run ruff check . && uv run ruff format .   # lint / format
```

## Deploy

GitHub Actions handles it: every push/PR runs lint + tests (`ci.yml`); pushes to
`master` build the image, publish it to GHCR, and restart the bot on the VM over SSH
(`deploy.yml`).

One-time setup:

- **VM**: install Docker, create `~/telegram_carousel_bot/` containing
  `docker-compose.yml` and a `.env` with the real `BOT_TOKEN`. If the GHCR package is
  private, run `docker login ghcr.io` once with a read-only token.
- **GitHub repo secrets**: `VM_HOST`, `VM_USER`, `VM_SSH_KEY` (private key whose public
  half is in the VM user's `authorized_keys`).

The bot is stateless — no volumes, no database; redeploys are free of migrations.
