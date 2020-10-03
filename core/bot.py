import discord
from discord.ext import commands
from discord.ext.commands.errors import (
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
    "cogs.commands",
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

        print(f"{message.channel}: {message.author}: {message.clean_content}")

        await self.process_commands(message)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx: commands.Context = await self.get_context(message=message)

        if ctx.command is None:
            return

        try:
            await self.invoke(ctx)
        finally:
            print(f"@{ctx.author} used {ctx.command.name} command in #{ctx.channel}")

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
                description=f"{ctx.author} raised this error that you didnt think of.",
                colour=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            error_embed.set_author(name="on_command_error")
            error_embed.add_field(name="Type", value=type(error).__name__)
            error_embed.add_field(name="Error", value=str(error))
            error_embed.add_field(name="Channel", value=ctx.channel.mention)
            error_embed.add_field(name="Message", value=f"[{ctx.message.id}]({ctx.message.jump_url})")
            await self.get_user(self.owner_id).send(embed=error_embed)
            raise error

    async def on_guild_join(self, guild: discord.Guild):
        for channel in guild.channels:
            try:
                invite: discord.Invite = await channel.create_invite()
            except discord.NotFound:
                continue
            else:
                break
        print(f"Joined guild {guild.name}, invite: {invite.url}")
        embed = self.embed(title=f"Joined guild {guild.name!r}", description=f"[Join here]({invite.url})")
        embed.set_author(name=guild.id)
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        await self.get_user(self.owner_id).send(embed=embed)

    @staticmethod
    def lts(list_: list):
        """List to string.
           For use in `self.on_command_error`"""
        return ', '.join([obj.name if isinstance(obj, discord.Role) else str(obj).replace('_', ' ') for obj in list_])

    @staticmethod
    def embed(*, ctx=None, title, description, color=0xFCD207) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            colour=color,
            timestamp=datetime.datetime.utcnow()
        )
        if ctx:
            embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Called by: {ctx.author}")
        return embed
