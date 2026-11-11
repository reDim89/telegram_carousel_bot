#!/usr/bin/env bash
# Pull-based deploy: fast-forward the deploy checkout to origin/master and
# restart the bot if anything changed. Run by telegram-carousel-bot-update.timer.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/services/telegram_carousel_bot}"
BRANCH="${BRANCH:-master}"
UV="${UV:-$HOME/.local/bin/uv}"
SERVICE=telegram-carousel-bot.service

cd "$APP_DIR"
git fetch --quiet origin "$BRANCH"
old=$(git rev-parse HEAD)
new=$(git rev-parse "origin/$BRANCH")
if [ "$old" = "$new" ]; then
    exit 0
fi

echo "Deploying $old -> $new"
git reset --quiet --hard "$new"
"$UV" sync --frozen --no-dev
if [ -f .env ]; then
    systemctl --user restart "$SERVICE"
    echo "Restarted $SERVICE at $new"
else
    echo "No .env yet; code updated but $SERVICE not started"
fi
