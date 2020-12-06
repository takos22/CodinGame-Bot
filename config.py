import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    TOKEN = os.environ.get("TOKEN", None)
    if TOKEN is None:
        raise RuntimeError("`TOKEN` environment variable isn't set")

    DEFAULT_COGS = [
        "jishaku",
        "cogs._help",
        "cogs.commands",
        "cogs.codingame",
        "cogs.log",
        "cogs.moderation",
    ]

    OWNER = 401346079733317634
    GUILD = 754028526079836251
    SERVER_LOG_CHANNEL = 754240215056384001
    MOD_LOG_CHANNEL = 754240243615662142
