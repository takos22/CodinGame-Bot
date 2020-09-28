import discord
from discord.ext import commands

import asyncio
import datetime
import os

initial_cogs = [
    "jishaku",
    "core.cogs._help",
    "core.cogs.codingame",
]

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=kwargs.pop("command_prefix", "!"), case_insensitive=True, **kwargs)
        self.start_time = datetime.datetime.utcnow()

    async def on_ready(self):
        print(f"Successfully logged in as {self.user}")
        for ext in initial_cogs:
            self.load_extension(ext)
        await self.cogs["CodinGame"].start()
        await self.change_presence(activity=discord.Game(name="!help"))

    async def on_message(self, message):
        await self.wait_until_ready()
        if message.author.bot:
            return
        print(f"{message.channel}: {message.author}: {message.clean_content}")
        if not message.guild:
            return
        await self.process_commands(message)

    async def logout(self):
        await self.cogs["CodinGame"].close()
        await super().logout()

    async def on_disconnect(self):
        print("Successfully logged out")
