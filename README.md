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

The bot runs on a self-hosted Linux machine as a **systemd user service** (no Docker,
no root), and deploys are pull-based: a systemd timer checks `origin/master` every
couple of minutes, and on a new commit fast-forwards the deploy checkout, runs
`uv sync`, and restarts the bot. GitHub Actions only runs lint + tests (`ci.yml`);
nothing connects into the machine, so there are no deploy secrets and no open ports.

One-time setup on the machine (needs `git` and [uv](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/reDim89/telegram_carousel_bot && cd telegram_carousel_bot
./deploy/install.sh
install -m 600 /dev/null ~/services/telegram_carousel_bot/.env
echo 'BOT_TOKEN=...' >> ~/services/telegram_carousel_bot/.env   # real @BotFather token
systemctl --user start telegram-carousel-bot
```

`install.sh` creates the deploy checkout in `~/services/telegram_carousel_bot`, installs
the units from `deploy/` into `~/.config/systemd/user`, and enables lingering so the bot
starts at boot without a login session. Re-run it after changing anything in `deploy/`.

```bash
systemctl --user status telegram-carousel-bot        # is it up?
journalctl --user -u telegram-carousel-bot -f        # bot logs
journalctl --user -u telegram-carousel-bot-update    # deploy history
```

Only one instance may poll a given bot token — stop any other deployment first.

The bot is stateless — no volumes, no database; redeploys are free of migrations.
