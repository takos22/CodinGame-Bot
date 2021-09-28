import discord
from discord.ext import commands

import datetime
import typing
from functools import wraps

from config import Config

if typing.TYPE_CHECKING:
    from bot import CodinGameBot


def setup(bot: "CodinGameBot"):
    bot.add_cog(Moderation(bot=bot))


def moderation(func: typing.Callable):
    @wraps(func)
    async def wrapper(self: "Moderation", ctx: commands.Context, *args):
        if ctx.guild is None or ctx.guild.id != Config.GUILD:
            return

        await func(self, ctx, *args)

    return wrapper


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot: "CodinGameBot" = bot
        self.logger = self.bot.logger.getChild("moderation")

    # --------------------------------------------------------------------------
    # Class methods

    @property
    def log_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(Config.MOD_LOG_CHANNEL)

    def log_embed(
        self,
        action: str,
        user: discord.User,
        moderator: discord.User,
        reason: str,
        duration: datetime.timedelta = None,
    ) -> discord.Embed:
        colors = {
            "warn": discord.Colour.gold(),
            "kick": discord.Colour.orange(),
            "mute": 0x000000,
            "unmute": discord.Colour.green(),
            "ban": discord.Colour.red(),
            "unban": discord.Colour.green(),
        }
        embed = self.bot.embed(
            title=f"**{action.title()}**",
            description=user.mention,
            color=colors[action],
            footer=f"ID: {user.id}",
        )

        embed.add_field(name="User", value=user)
        embed.add_field(name="Moderator", value=moderator.mention)
        embed.add_field(name="Reason", value=reason)
        if duration:
            embed.add_field(name="Duration", value=duration)

        embed.set_author(name=user, icon_url=user.avatar_url)

        return embed

    def success_embed(
        self,
        action: str,
        user: discord.User,
    ) -> discord.Embed:
        verbs = {
            "warn": "warned",
            "kick": "kicked",
            "mute": "muted",
            "unmute": "unmuted",
            "ban": "banned",
            "unban": "unbanned",
        }
        embed = self.bot.embed(
            title=f"**{user}** was {verbs[action]}.",
            colour=discord.Colour.green(),
        )

        return embed

    async def cog_check(self, ctx) -> bool:
        return ctx.guild is not None

    # --------------------------------------------------------------------------
    # Commands

    @commands.command("purge")
    @commands.has_guild_permissions(manage_messages=True)
    @moderation()
    async def purge(self, ctx: commands.Context, number_of_messages: int):
        """Delete a number of messages (limit: 1000)"""

        await ctx.channel.purge(limit=number_of_messages, before=ctx.message)
        await ctx.message.delete()
        self.logger.info(
            f"channel `{ctx.channel}` purged of `{number_of_messages}` messages by `{ctx.author}`"
        )

    @commands.command("kick")
    @commands.has_guild_permissions(kick_members=True)
    @moderation()
    async def kick(
        self, ctx: commands.Context, user: discord.Member, *, reason: str = None
    ):
        """Kick a member with an optional reason"""

        # Checks
        if user == self.bot.user:
            return await ctx.send("I can't kick myself")

        if user == ctx.author:
            return await ctx.send("You can't kick yourself")

        if user.top_role.position >= ctx.author.top_role.position:
            return await ctx.send(
                "You can't kick a user who has a higher role than you"
            )

        # Kick
        await ctx.guild.kick(user, reason=reason)
        await ctx.message.delete()

        # DM the user
        try:
            await user.send(
                f"You were kicked from {ctx.guild.name} for reason: {reason}"
            )
        except discord.Forbidden:
            self.logger.info(
                f"user `{user}` kicked from guild `{ctx.guild}` "
                f"for reason `{reason}` (couldn't DM them)"
            )
        else:
            self.logger.info(
                f"user `{user}` kicked from guild `{ctx.guild}` for reason `{reason}`"
            )

        # Success embed
        success_embed = self.success_embed("kick", user)
        await ctx.send(embed=success_embed)

        # Modlog embed
        log_embed = self.log_embed("kick", user, ctx.author, reason)
        await self.log_channel.send(embed=log_embed)

    @commands.command("ban")
    @commands.has_guild_permissions(ban_members=True)
    @moderation()
    async def ban(
        self,
        ctx: commands.Context,
        user: discord.User,
        delete_message_days: str = "1",
        *,
        reason: str = None,
    ):
        """Ban a member with an optional reason"""

        # Compute the `delete_message_days` and the `reason`
        if delete_message_days.isdigit():
            delete_message_days = int(delete_message_days)
        else:
            reason = reason or ""
            reason = delete_message_days + reason
            delete_message_days = 1

        # Checks
        if user == self.bot.user:
            return await ctx.send("I can't ban myself")

        if user == ctx.author:
            return await ctx.send("You can't ban yourself")

        member: discord.Member = ctx.guild.get_member(user.id)
        if member and member.top_role.position >= ctx.author.top_role.position:
            return await ctx.send(
                "You can't ban a user who has a higher role than you"
            )

        bans = await ctx.guild.bans()
        if user.id in {ban.user.id for ban in bans}:
            return await ctx.send("User is already banned")

        # Ban
        await ctx.guild.ban(
            user, reason=reason, delete_message_days=delete_message_days
        )
        await ctx.message.delete()

        # DM the user
        try:
            await user.send(
                f"You were banned from {ctx.guild.name} for reason: {reason}"
            )
        except discord.Forbidden:
            self.logger.info(
                f"user `{user}` banned from guild `{ctx.guild}` "
                f"for reason `{reason}` (couldn't DM them)"
            )
        else:
            self.logger.info(
                f"user `{user}` banned from guild `{ctx.guild}` for reason `{reason}`"
            )

        # Success embed
        success_embed = self.success_embed("ban", user)
        await ctx.send(embed=success_embed)

        # Modlog embed
        log_embed = self.log_embed("ban", user, ctx.author, reason)
        await self.log_channel.send(embed=log_embed)

    @commands.command("unban")
    @commands.has_guild_permissions(ban_members=True)
    @moderation()
    async def unban(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str = None,
    ):
        """Unban a member with an optional reason"""

        # Unban
        await ctx.guild.unban(user, reason=reason)
        await ctx.message.delete()

        # DM the user
        try:
            await user.send(
                f"You were unbanned from {ctx.guild.name} for reason: {reason}"
            )
        except discord.Forbidden:
            self.logger.info(
                f"user `{user}` unbanned from guild `{ctx.guild}` "
                f"for reason `{reason}` (couldn't DM them)"
            )
        else:
            self.logger.info(
                f"user `{user}` unbannned from guild `{ctx.guild}` for reason `{reason}`"
            )

        # Success embed
        success_embed = self.success_embed("unban", user)
        await ctx.send(embed=success_embed)

        # Modlog embed
        log_embed = self.log_embed("unban", user, ctx.author, reason)
        await self.log_channel.send(embed=log_embed)

    # ---------------------------------------------------------------------------------------------
    # Command errors

    @kick.error
    async def kick_error(self, ctx: commands.Context, error):
        error = getattr(error, "original", error)
        self.logger.warning(
            f"command `{ctx.command.name}` raised exception: {error}"
        )

        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send_help("kick")

        elif isinstance(error, commands.errors.MemberNotFound):
            return await ctx.send("User not found")

        elif isinstance(error, discord.Forbidden):
            return await ctx.send("User is higher than the bot")

        else:
            await self.bot.handle_error(error, ctx=ctx)

    @ban.error
    async def ban_error(self, ctx: commands.Context, error):
        error = getattr(error, "original", error)
        self.logger.warning(
            f"command `{ctx.command.name}` raised exception: {error}"
        )

        # Missing argument
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send_help("ban")

        # User not found
        elif isinstance(error, commands.errors.UserNotFound):
            try:
                id = int(error.argument)
                user = await self.bot.fetch_user(id)
                assert user is not None
            except (ValueError, AssertionError):
                return await ctx.send("User not found, you should use their id")
            else:
                # Reinvoke if the user is found
                delete_message_days, *reason = (
                    error.argument.join(
                        ctx.message.content.split(error.argument)[1:]
                    )
                    .lstrip()
                    .split()
                )
                reason = " ".join(reason)
                await ctx.invoke(
                    ctx.command, user, delete_message_days, reason=reason
                )

        # Can't ban
        elif isinstance(error, discord.Forbidden):
            return await ctx.send("User is higher than the bot")

        else:
            await self.bot.handle_error(error, ctx=ctx)

    @unban.error
    async def unban_error(self, ctx: commands.Context, error):
        error = getattr(error, "original", error)
        self.logger.warning(
            f"command `{ctx.command.name}` raised exception: {error}"
        )

        # Missing argument
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send_help("unban")

        # User not found
        elif isinstance(error, commands.errors.UserNotFound):
            try:
                id = int(error.argument)
                user = await self.bot.fetch_user(id)
                assert user is not None
            except (ValueError, AssertionError):
                return await ctx.send("User not found, you should use their id")
            else:
                # Reinvoke if the user is found
                reason = error.argument.join(
                    ctx.message.content.split(error.argument)[1:]
                ).lstrip()

                await ctx.invoke(ctx.command, user, reason=reason)

        # User not banned
        elif isinstance(error, discord.errors.NotFound):
            return await ctx.send("User isn't banned")

        else:
            await self.bot.handle_error(error, ctx=ctx)
