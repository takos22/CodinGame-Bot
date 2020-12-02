import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    TOKEN = os.environ.get("TOKEN")

    DEFAULT_COGS = [
        "jishaku",
        "cogs._help",
        "cogs.commands",
        "cogs.codingame",
        "cogs.log",
    ]

    OWNER = 401346079733317634
    GUILD = 754028526079836251
    SERVER_LOG_CHANNEL = 754240215056384001
