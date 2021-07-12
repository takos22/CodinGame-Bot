import discord
from discord.ext import commands

import codingame
import datetime
import functools
import logging
import logging.handlers
import os
import sys
import traceback
import typing

from config import Config
from utils import indent, color, NoColorFormatter

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class CodinGameBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=Config.PREFIX,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_id=Config.OWNER_ID,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False
            ),
            **kwargs,
        )
        self.start_time: datetime = datetime.datetime.now(datetime.timezone.utc)
        self.cg_client: typing.Optional[codingame.Client] = None

        self.init_log(Config.LOG_LEVEL)

    def init_log(self, level=logging.INFO):
        self.logger: logging.Logger = logging.getLogger("bot")
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Formatters
        formatter = logging.Formatter(
            fmt="[{asctime}.{msecs:0>3.0f}] {name:>15}: {levelname:>8}: {message}",  # noqa: E501
            datefmt="%d/%m/%Y %H:%M:%S",
            style="{",
        )
        file_formatter = NoColorFormatter(
            fmt="[{asctime}.{msecs:0>3.0f}] {name:>15}: {levelname:>8}: {message}",  # noqa: E501
            datefmt="%d/%m/%Y %H:%M:%S",
            style="{",
        )

        # INFO file handler
        file_handler = logging.FileHandler(
            "log/root.log", mode="w", encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # DEBUG stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)

        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

        # ERROR stderr handler
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)

        stderr_handler.setFormatter(formatter)
        self.logger.addHandler(stderr_handler)

        # ERROR file handler
        error_handler = logging.handlers.RotatingFileHandler(
            "log/error.log", maxBytes=2 ** 16, backupCount=10, encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)

        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)

        # Child loggers
        self.message_logger = self.logger.getChild("message")
        self.command_logger = self.logger.getChild("command")

    # --------------------------------------------------------------------------
    # Cogs

    def add_cog(self, cog):
        super().add_cog(cog)
        self.logger.debug(color(f"loaded cog `{cog.__cog_name__}`", "cyan"))

    def remove_cog(self, name):
        super().remove_cog(name)
        self.logger.debug(color(f"loaded cog `{name}`", "yellow"))

    # --------------------------------------------------------------------------
    # Events

    async def on_ready(self):
        self.cg_client = codingame.Client(is_async=True)

        for cog in Config.DEFAULT_COGS:
            self.load_extension(cog)

        self.logger.info(color("loaded all cogs", "green"))

        await self.change_presence(
            activity=discord.Game(name=f"{Config.PREFIX}help")
        )
        self.logger.debug(color(f"set status to `{Config.PREFIX}help`", "cyan"))

        self.logger.info(color(f"logged in as user `{self.user}`", "green"))

    async def close(self):
        await self.cg_client.close()
        await super().close()
        self.logger.info(color("logged out", "red"))

    async def on_message(self, message: discord.Message):
        await self.wait_until_ready()

        if message.author.bot:
            return

        message_info: str = (
            (
                f"{message.guild} ({message.guild.id}): "
                if message.guild is not None
                else ""
            )
            + f"#{message.channel} ({message.channel.id}): "
            + f"@{message.author} ({message.author.id}): "
        )

        message_text: str = indent(
            message.content or "\n".join([a.url for a in message.attachments]),
            49,
        )

        self.message_logger.info(color(message_info, "cyan") + message_text)

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx: commands.Context = await self.get_context(message=message)

        if ctx.command is None:
            return

        ctx.full_name = " ".join(ctx.invoked_parents + [ctx.invoked_with])

        command_info: str = (
            (f"{ctx.guild} ({ctx.guild.id}): " if ctx.guild is not None else "")
            + f"#{ctx.channel} ({ctx.channel.id}): "
            + f"@{ctx.author} ({ctx.author.id}): "
            + "command `"
            + ctx.full_name
            + "`"
        )

        self.command_logger.info(color(command_info, "purple"))

        try:
            await self.invoke(ctx)
        except Exception as exc:
            await self.dispatch("command_error", ctx, exc)

    async def on_command_error(
        self, ctx: commands.Context, exception: Exception
    ):
        await self.wait_until_ready()
        send = functools.partial(
            ctx.send, reference=ctx.message, mention_author=True
        )

        error = getattr(exception, "original", exception)

        self.command_logger.warning(
            f"{ctx.full_name} raised exception: {exception}",
            exc_info=(type(exception), exception, exception.__traceback__),
        )

        if isinstance(error, commands.CheckFailure):
            return

        elif isinstance(
            error,
            (
                commands.BadUnionArgument,
                commands.CommandOnCooldown,
                commands.PrivateMessageOnly,
                commands.NoPrivateMessage,
                commands.MissingRequiredArgument,
                commands.ConversionError,
            ),
        ):
            return await send(str(error))

        elif isinstance(error, commands.BotMissingPermissions):
            return await send(
                "I am missing these permissions to do this command:"
                f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, commands.MissingPermissions):
            return await send(
                "You are missing these permissions to do this command:"
                f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(
            error, (commands.BotMissingAnyRole, commands.BotMissingRole)
        ):
            return await send(
                f"I am missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )

        elif isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            return await send(
                f"You are missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )
        else:
            await send(
                "An unexpected error occured, developers have been informed"
            )
            await self.handle_error(error, ctx=ctx)

    # --------------------------------------------------------------------------
    # Helper methods

    async def handle_error(
        self, exception: Exception, *, ctx: commands.Context = None
    ):
        self.logger.exception(
            "Unhandled error",
            exc_info=(type(exception), exception, exception.__traceback__),
        )
        stack = traceback.extract_tb(exception.__traceback__)

        error_embed = self.embed(
            title="Unhandled error",
            description=f"`{stack[-1].name}` raised an unhandled error",
            color=discord.Colour.red(),
        )

        error_embed.set_author(
            name='File "{0.filename}", line {0.lineno} in {0.name}'.format(
                stack[-1]
            )
        )

        if ctx:
            error_embed.description = (
                f"`{ctx.full_name}` command raised an unhandled error"
            )
            error_embed.add_field(
                name="Channel",
                value=ctx.channel.mention
                if ctx.guild is not None
                else f"Private message with {ctx.author}",
                inline=True,
            )
            error_embed.add_field(
                name="Message",
                value=f"[{ctx.message.id}]({ctx.message.jump_url})",
                inline=True,
            )

        error_embed.add_field(
            name="Type", value=f"`{type(exception).__name__}`", inline=True
        )
        error_embed.add_field(name="Error", value=f"`{exception}`", inline=True)

        tb = "".join(traceback.format_tb(exception.__traceback__))
        if len(tb) + 9 > 1024:
            for limit in range(-len(stack), 0):
                tb = "".join(
                    traceback.format_tb(exception.__traceback__, limit)
                )
                if len(tb) + 9 <= 1024:
                    break

        error_embed.add_field(
            name="Full traceback",
            value=f"```py\n{tb}```",
            inline=False,
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
                obj.name
                if isinstance(obj, discord.Role)
                else str(obj).replace("_", " ")
                for obj in list_
            ]
        )

    @staticmethod
    def embed(
        *,
        title: str = "",
        description: str = "",
        color: typing.Union[discord.Colour, int] = 0xFCD207,
        add_timestamp: bool = True,
        ctx: commands.Context = None,
    ) -> discord.Embed:
        kwargs = {"color": color}
        if title:
            kwargs["title"] = title
        if description:
            kwargs["description"] = description
        if add_timestamp:
            kwargs["timestamp"] = datetime.datetime.now(datetime.timezone.utc)

        embed = discord.Embed(**kwargs)
        if ctx:
            embed.set_footer(
                icon_url=ctx.author.avatar_url, text=f"Called by: {ctx.author}"
            )

        return embed


if __name__ == "__main__":
    bot = CodinGameBot()
    bot.run(Config.TOKEN)
