import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_token: str


def load_config() -> Config:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    return Config(bot_token=token)
