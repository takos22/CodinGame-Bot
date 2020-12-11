import discord
from discord.ext import commands
from discord.ext.commands.errors import (
    BadUnionArgument,
    BotMissingAnyRole,
    BotMissingPermissions,
    BotMissingRole,
    CheckFailure,
    CommandOnCooldown,
    ConversionError,
    MissingAnyRole,
    MissingPermissions,
    MissingRequiredArgument,
    MissingRole,
    NoPrivateMessage,
    PrivateMessageOnly,
)

import datetime
import logging
import logging.handlers
import os
import pprint
import sys
import traceback
import typing

from config import Config
from utils import indent, shorten, color

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=kwargs.pop("command_prefix", "!"),
            case_insensitive=True,
            intents=discord.Intents.all(),
            **kwargs,
        )
        self.start_time = datetime.datetime.utcnow()
        self.config: Config = kwargs.pop("config")
        self.owner_id = self.config.OWNER

        self.init_log(kwargs.pop("log_level", logging.INFO))

        self.logger.info(color("bot started", "green"))

    def init_log(self, level=logging.INFO):
        self.logger = logging.getLogger("bot")
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Formatters
        formatter = logging.Formatter(
            fmt="[{asctime}.{msecs:0>3.0f}] {name:<15}: {levelname}: {message}",
            datefmt="%d/%m/%Y %H:%M:%S",
            style="{",
        )
        error_formatter = logging.Formatter(
            fmt="[{asctime}.{msecs:0>3.0f}] {name:<15}: {levelname}:\n{message}",
            datefmt="%d/%m/%Y %H:%M:%S",
            style="{",
        )

        # INFO file handler
        file_handler = logging.FileHandler("log/root.log", mode="w", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # DEBUG stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)

        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

        # ERROR stderr handler
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)

        stderr_handler.setFormatter(error_formatter)
        self.logger.addHandler(stderr_handler)

        # ERROR file handler
        error_handler = logging.handlers.RotatingFileHandler(
            "log/error.log", maxBytes=2 ** 16, backupCount=10, encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)

        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

        # Child loggers
        self.message_logger = self.logger.getChild("message")
        self.command_logger = self.logger.getChild("command")

    # ---------------------------------------------------------------------------------------------
    # Events

    async def on_ready(self):
        self.logger.info(color(f"logged in as user `{self.user}`", "green"))

        for ext in self.config.DEFAULT_COGS:
            self.load_extension(ext)
        await self.cogs["CodinGame"].start()
        self.logger.info(color("all cogs loaded", "green"))

        await self.change_presence(activity=discord.Game(name="!help"))

        await self.cogs["Log"].log_channel.send(
            embed=self.cogs["Log"].log_embed(
                "create", title=f"`[{self.config.ENV}]` Bot is online", user=self.user
            )
        )

    async def logout(self):
        await self.cogs["CodinGame"].close()

        await self.cogs["Log"].log_channel.send(
            embed=self.cogs["Log"].log_embed(
                "delete", title=f"`[{self.config.ENV}]` Bot is offline", user=self.user
            )
        )

        await super().logout()
        self.logger.info(color("logged out", "green"))

    async def on_message(self, message: discord.Message):
        await self.wait_until_ready()

        if message.author.bot:
            return

        message_text = indent(
            message.clean_content
            or "\n".join([a.url for a in message.attachments])
            or "\n".join([pprint.pformat(e.to_dict(), width=120) for e in message.embeds]),
            49,
        )

        self.message_logger.info(
            color(f"user `{message.author}` in channel `{message.channel}`:\n", "cyan")
            + message_text
        )

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx: commands.Context = await self.get_context(message=message)

        if ctx.command is None:
            return

        self.command_logger.info(
            color(
                f"user `{ctx.author}` in channel `{ctx.channel}`: command "
                f"`{(ctx.command.parent.name + ' ') if ctx.command.parent else ''}"
                f"{ctx.command.name}` used",
                "purple",
            )
        )

        await self.invoke(ctx)

    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        await self.wait_until_ready()

        error = getattr(exception, "original", exception)

        if hasattr(ctx.command, "on_error"):
            return

        self.command_logger.warning(f"{ctx.command.name} raised exception: {error}")

        if isinstance(error, CheckFailure):
            return

        elif isinstance(
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
                "I am missing these permissions to do this command:"
                f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, MissingPermissions):
            return await ctx.send(
                "You are missing these permissions to do this command:"
                f"\n{self.lts(error.missing_perms)}"
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
            await self.handle_error(error)

    # ---------------------------------------------------------------------------------------------
    # Helper methods

    async def handle_error(self, error: Exception, *, ctx: commands.Context = None):
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        self.logger.error(color("Unhandled error:\n" + "".join(tb), "red"))
        stack = traceback.extract_tb(error.__traceback__)

        error_embed = discord.Embed(
            title="Unhandled error",
            description=f"`{stack[-1].name}` function raised an unhandled error",
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.utcnow(),
        )

        error_embed.set_author(
            name=f'File "{stack[-1].filename}", line {stack[-1].lineno} in {stack[-1].name}'
        )
        error_embed.add_field(name="Type", value=f"`{type(error).__name__}`", inline=False)
        error_embed.add_field(name="Error", value=f"`{error}`", inline=False)
        error_embed.add_field(
            name="Full traceback",
            value=f"```py\n{shorten(''.join(tb), width=1015, placeholder='...')}```",
            inline=False,
        )

        if ctx:
            error_embed.description = f"`{ctx.command.name}` command raised an unhandled error"
            error_embed.add_field(name="Channel", value=ctx.channel.mention, inline=False)
            error_embed.add_field(
                name="Message", value=f"[{ctx.message.id}]({ctx.message.jump_url})", inline=False
            )

        await self.owner.send(embed=error_embed)

    @property
    def owner(self) -> discord.User:
        return self.get_user(self.owner_id)

    @staticmethod
    def lts(list_: list) -> str:
        """List to string.
        For use in `self.on_command_error`"""
        return ", ".join(
            [
                obj.name if isinstance(obj, discord.Role) else str(obj).replace("_", " ")
                for obj in list_
            ]
        )

    @staticmethod
    def embed(
        *,
        ctx: commands.Context = None,
        title: str = None,
        description: str = None,
        color: typing.Union[discord.Colour, int] = 0xFCD207,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=title, description=description, colour=color, timestamp=datetime.datetime.utcnow()
        )
        if ctx:
            embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Called by: {ctx.author}")
        return embed
