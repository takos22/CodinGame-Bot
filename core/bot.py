import discord
from discord.ext import commands
from discord.errors import (
    CheckFailure,
    BadUnionArgument,
    CommandOnCooldown,
    PrivateMessageOnly,
    NoPrivateMessage,
    MissingRequiredArgument,
    ConversionError,
    BotMissingPermissions,
    MissingPermissions,
    BotMissingAnyRole,
    BotMissingRole,
    MissingRole,
    MissingAnyRole,
)

import datetime
import os

initial_cogs = [
    "jishaku",
    "cogs._help",
    "cogs.codingame",
]

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=kwargs.pop("command_prefix", "!"), case_insensitive=True, **kwargs)
        self.start_time = datetime.datetime.utcnow()
        self.owner_id = 401346079733317634

    async def on_ready(self):
        print(f"Successfully logged in as {self.user}")

        for ext in initial_cogs:
            self.load_extension(ext)
        await self.cogs["CodinGame"].start()
        print("Successfully loaded cogs")

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

    async def on_command_error(self, ctx, exception):
        await self.wait_until_ready()

        error = getattr(exception, "original", exception)

        if hasattr(ctx.command, "on_error"):
            return

        elif isinstance(error, CheckFailure):
            return

        if isinstance(
            error,
            (
                BadUnionArgument,
                CommandOnCooldown,
                PrivateMessageOnly,
                NoPrivateMessage,
                MissingRequiredArgument,
                ConversionError,
            ),
        ):
            return await ctx.send(str(error))

        elif isinstance(error, BotMissingPermissions):
            return await ctx.send(
                "I am missing these permissions to do this command:" f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, MissingPermissions):
            return await ctx.send(
                "You are missing these permissions to do this command:" f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, (BotMissingAnyRole, BotMissingRole)):
            return await ctx.send(
                f"I am missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )

        elif isinstance(error, (MissingRole, MissingAnyRole)):
            return await ctx.send(
                f"You are missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )

        else:
            error_embed = discord.Embed(
                title="Error you didn't think of",
                description=f"{self.context.author} raised this error that you didnt think of.",
                colour=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            error_embed.set_author(name="send_command_help")
            error_embed.add_field(name="Type", value=type(error).__name__)
            error_embed.add_field(name="Error", value=str(error))
            error_embed.add_field(name="Channel", value=self.context.channel.mention)
            error_embed.add_field(name="Message", value=f"[{self.context.message.id}]({self.context.message.jump_url})")
            await self.get_user(self.owner_id).send(embed=error_embed)
            raise error

    @staticmethod
    def embed(ctx, *, title, description, color=0xFCD207) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            colour=color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Called by: {ctx.author}")
        return embed
