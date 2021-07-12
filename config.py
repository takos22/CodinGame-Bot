import logging
import os
import typing

from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV: typing.List[str] = [
    "TOKEN",
]

for env in REQUIRED_ENV:
    if env not in os.environ:
        raise RuntimeError(f"Missing environment variable `{env}`")

DEV = bool(int(os.environ.get("DEV", "0")))

class BaseConfig:
    # Bot
    TOKEN: str = os.environ.get("TOKEN")
    PREFIX: str
    OWNER_ID: int = 401346079733317634
    LOG_LEVEL: int

    DEFAULT_COGS = [
        "jishaku",
        "cogs._help",
        "cogs.commands",
        "cogs.codingame",
        "cogs.log",
        "cogs.moderation",
    ]

    # Guild
    GUILD: int
    SERVER_LOG_CHANNEL: int
    MOD_LOG_CHANNEL: int

class ProdConfig(BaseConfig):
    PREFIX = "!"
    LOG_LEVEL = logging.INFO

    # Guild
    GUILD = 754028526079836251
    SERVER_LOG_CHANNEL = 754240215056384001
    MOD_LOG_CHANNEL = 754240243615662142

class DevConfig(BaseConfig):
    PREFIX = os.environ.get("PREFIX", "!")
    LOG_LEVEL = logging.DEBUG

    # Guild
    GUILD = 754028526079836251
    SERVER_LOG_CHANNEL = 754240215056384001
    MOD_LOG_CHANNEL = 754240243615662142

Config: typing.Type[BaseConfig] = DevConfig if DEV else ProdConfig
