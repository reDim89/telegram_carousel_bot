#!/usr/bin/env bash
# One-time setup of the bot on this machine (no root, no Docker needed).
# Requires git and uv (https://docs.astral.sh/uv/) for the current user.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/reDim89/telegram_carousel_bot}"
APP_DIR="${APP_DIR:-$HOME/services/telegram_carousel_bot}"
UV="${UV:-$HOME/.local/bin/uv}"
SRC="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$APP_DIR/.git" ]; then
    mkdir -p "$(dirname "$APP_DIR")"
    git clone --branch master "$REPO_URL" "$APP_DIR"
fi
(cd "$APP_DIR" && "$UV" sync --frozen --no-dev)

install -Dm755 "$SRC/update.sh" "$HOME/.local/bin/telegram-carousel-bot-update"
install -Dm644 -t "$HOME/.config/systemd/user" \
    "$SRC/telegram-carousel-bot.service" \
    "$SRC/telegram-carousel-bot-update.service" \
    "$SRC/telegram-carousel-bot-update.timer"

systemctl --user daemon-reload
systemctl --user enable --now telegram-carousel-bot-update.timer
systemctl --user enable telegram-carousel-bot.service
# Keep user services running without an open login session.
loginctl enable-linger "$USER" || echo "Could not enable linger; run: sudo loginctl enable-linger $USER"

if [ -f "$APP_DIR/.env" ]; then
    systemctl --user restart telegram-carousel-bot.service
else
    echo "Now create $APP_DIR/.env with BOT_TOKEN=... (chmod 600), then run:"
    echo "  systemctl --user start telegram-carousel-bot"
fi
