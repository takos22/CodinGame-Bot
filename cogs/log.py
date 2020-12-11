import discord
from discord.ext import commands

import datetime
import typing
from functools import wraps

from core import Bot
from utils import indent, color


def setup(bot: Bot):
    bot.add_cog(Log(bot=bot))


def log(func: typing.Callable):
    @wraps(func)
    async def wrapper(self: "Log", *args):
        if isinstance(args[0], list):
            # bulk message delete
            guild = args[0][0].guild
        elif isinstance(args[0], discord.Guild):
            # ban, unban, available, unavailable
            guild = args[0]
        else:
            guild = args[0].guild

        if guild is None or guild.id != self.bot.config.GUILD:
            return

        try:
            await func(self, *args)
        except Exception as error:
            await self.bot.handle_error(error)

    return wrapper


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.logger = self.bot.logger.getChild("log")
        self.logger.info(color("cog `Log` loaded", "blue"))

    def cog_unload(self):
        self.logger.info(color("cog `Log` unloaded", "yellow"))

    # ---------------------------------------------------------------------------------------------
    # Class methods

    @property
    def log_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.bot.config.SERVER_LOG_CHANNEL)

    @staticmethod
    def log_embed(
        log_type: str,
        *,
        title: str = None,
        description: str = None,
        footer: str = None,
        user: discord.User = None,
        guild: discord.Guild = None,
    ) -> discord.Embed:
        colors = {
            "create": discord.Colour.green(),
            "edit": discord.Colour.blue(),
            "delete": discord.Colour.red(),
        }
        embed = discord.Embed(
            title=title,
            description=description,
            colour=colors[log_type],
            timestamp=datetime.datetime.utcnow(),
        )

        if footer:
            embed.set_footer(text=footer)

        if user:
            embed.set_author(name=user, icon_url=user.avatar_url)
        elif guild:
            embed.set_author(name=guild.name, icon_url=guild.icon_url)

        return embed

    @staticmethod
    def to_dict(obj, sort=True) -> dict:
        attrs = sorted(dir(obj)) if sort else dir(obj)
        return {attr: getattr(obj, attr, None) for attr in attrs}

    @staticmethod
    def perms_to_str(permissions: discord.Permissions) -> str:
        return "\n".join(
            [
                f"{name.replace('_', ' ').title() + ' ':.<22} {str(value).lower()}"
                for name, value in sorted(permissions)
            ]
        )

    @property
    def role_desc(self) -> str:
        return (
            "Name: `{name}`\nHoist: `{hoist}`\nPosition (counted from the bottom): "
            "`{position}`\nMentionable: `{mentionable}`\nColor: `#{colour}`\n"
            "Permissions:```prolog\n{perms}```"
        )

    # ---------------------------------------------------------------------------------------------
    # Message events

    @commands.Cog.listener()
    @log
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return

        self.logger.info(
            color(
                f"message edited by user `{before.author}` in channel `{before.channel}`\n", "blue"
            )
            + indent(f"before: {before.content}\nafter: {after.content}", 49)
        )

        if before.content == after.content:
            return

        log_embed = self.log_embed(
            "edit",
            description=(
                f"**Message sent by {before.author.mention} "
                f"edited in {before.channel.mention}**\n"
                f"[Jump to message]({after.jump_url})"
            ),
            footer=f"Channel ID: {before.channel.id} • Message ID: {before.id}",
            user=before.author,
        )

        log_embed.add_field(
            name="Before",
            value=f"{before.content:.1021}{'...' if len(before.content) > 1021 else ''}",
            inline=False,
        )
        log_embed.add_field(
            name="After",
            value=f"{after.content:.1021}{'...' if len(after.content) > 1021 else ''}",
            inline=False,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        self.logger.info(
            color(
                f"message deleted by user `{message.author}` in channel `{message.channel}`\n"
                "red",
            )
            + indent(f"content: {message.content}", 49),
        )

        log_embed = self.log_embed(
            "delete",
            description=(
                f"**Message sent by {message.author.mention} deleted "
                f"in {message.channel.mention}**\n"
                f"{message.content:.1972}"
            ),
            footer=f"Channel ID: {message.channel.id} • Message ID: {message.id}",
            user=message.author,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_bulk_message_delete(self, messages: typing.List[discord.Message]):
        self.logger.info(
            color(
                f"bulk message delete in channel `{messages[0].channel}` ({len(messages)})",
                "red",
            )
        )

        log_embed = self.log_embed(
            "delete",
            description=(
                f"**Bulk message delete in {messages[0].channel.mention}**\n"
                f"{len(messages)} messages deleted"
            ),
            footer=f"Channel ID: {messages[0].channel.id}",
            guild=messages[0].guild,
        )

        await self.log_channel.send(embed=log_embed)

    # ---------------------------------------------------------------------------------------------
    # Guild channel events

    @commands.Cog.listener()
    @log
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        self.logger.info(color(f"channel `{channel}` created", "green"))

        log_embed = self.log_embed(
            "create",
            description=f"**Channel created: #{channel} ({channel.__class__.__name__})**",
            footer=f"ID: {channel.id}",
            guild=channel.guild,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        self.logger.info(color(f"channel `{channel}` deleted", "red"))

        log_embed = self.log_embed(
            "delete",
            description=f"**Channel deleted: #{channel} ({channel.__class__.__name__})**",
            footer=f"ID: {channel.id}",
            guild=channel.guild,
        )

        await self.log_channel.send(embed=log_embed)

    # ---------------------------------------------------------------------------------------------
    # Guild role events

    @commands.Cog.listener()
    @log
    async def on_guild_role_create(self, role: discord.Role):
        self.logger.info(
            color(f"role `{role.name}` created:\n", "green")
            + indent(
                self.role_desc.format(
                    **self.to_dict(role), perms=self.perms_to_str(role.permissions)
                ).lower(),
                49,
            )
        )

        log_embed = self.log_embed(
            "create",
            description=f"**Role created: {role.name} ({role.mention})**",
            footer=f"ID: {role.id}",
            guild=role.guild,
        )
        log_embed.add_field(
            name="Info",
            value=self.role_desc.format(
                **self.to_dict(role), perms=self.perms_to_str(role.permissions)
            ),
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_guild_role_delete(self, role: discord.Role):
        self.logger.info(
            color(f"role `{role.name}` deleted:\n", "red")
            + indent(
                self.role_desc.format(
                    **self.to_dict(role), perms=self.perms_to_str(role.permissions)
                ).lower(),
                49,
            )
        )

        log_embed = self.log_embed(
            "delete",
            description=f"**Role deleted: {role.name}**",
            footer=f"ID: {role.id}",
            guild=role.guild,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        self.logger.info(
            color(f"role `{after.name}` edited:\n", "blue")
            + "Before: {}\nAfter: {}".format(
                indent(
                    self.role_desc.format(
                        **self.to_dict(before), perms=self.perms_to_str(before.permissions)
                    ).lower(),
                    49,
                ),
                indent(
                    self.role_desc.format(
                        **self.to_dict(after), perms=self.perms_to_str(after.permissions)
                    ).lower(),
                    49,
                ),
            )
        )

        log_embed = self.log_embed(
            "edit",
            description=f"**Role edited: {after.name} ({after.mention})**",
            footer=f"ID: {before.id}",
            guild=before.guild,
        )

        log_embed.add_field(
            name="Before",
            value=self.role_desc.format(
                **self.to_dict(before), perms=self.perms_to_str(before.permissions)
            ),
        )
        log_embed.add_field(
            name="After",
            value=self.role_desc.format(
                **self.to_dict(after), perms=self.perms_to_str(after.permissions)
            ),
        )

        await self.log_channel.send(embed=log_embed)

    # ---------------------------------------------------------------------------------------------
    # Guild available events

    @commands.Cog.listener()
    @log
    async def on_guild_available(self, guild: discord.Guild):
        self.logger.info(color(f"guild `{guild.name}` is available again", "green"))
        log_embed = self.log_embed(
            "create",
            description="**Guild is available again**",
            footer=f"ID: {guild.id}",
            guild=guild,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_guild_unavailable(self, guild: discord.Guild):
        self.logger.warning(color(f"guild `{guild.name}` is unavailable", "red"))
        log_embed = self.log_embed(
            "delete",
            description="**Guild is unavailable**",
            footer=f"ID: {guild.id}",
            guild=guild,
        )

        await self.log_channel.send(embed=log_embed)

    # ---------------------------------------------------------------------------------------------
    # Member events

    @commands.Cog.listener()
    @log
    async def on_member_join(self, member: discord.Member):
        self.logger.info(color(f"member `{member}` joined", "green"))
        log_embed = self.log_embed(
            "create",
            description=f"**Member joined: {member.mention} ({member})**",
            footer=f"ID: {member.id}",
            user=member,
        )

        account_age: datetime.timedelta = datetime.datetime.utcnow() - member.created_at
        log_embed.add_field(
            name="Account age",
            value=(
                (str(account_age.days) + " days, " if account_age.days else "")
                + (
                    str(account_age.seconds // 3600) + " hours, "
                    if account_age.seconds >= 3600
                    else ""
                )
                + (
                    str(account_age.seconds % 3600 // 60) + " mins, "
                    if account_age.seconds % 3600 >= 60
                    else ""
                )
                + (
                    str(account_age.seconds % 3600 % 60) + " sec"
                    if account_age.seconds % 3600 % 60
                    else ""
                )
            ),
            inline=False,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_member_remove(self, member: discord.Member):
        self.logger.info(color(f"member `{member}` left", "red"))
        log_embed = self.log_embed(
            "delete",
            description=f"**Member left: {member.mention} ({member})**",
            footer=f"ID: {member.id}",
            user=member,
        )

        stay_time: datetime.timedelta = datetime.datetime.utcnow() - member.joined_at
        log_embed.add_field(
            name="Time stayed",
            value=(
                (str(stay_time.days) + " days, " if stay_time.days else "")
                + (str(stay_time.seconds // 3600) + " hours, " if stay_time.seconds >= 3600 else "")
                + (
                    str(stay_time.seconds % 3600 // 60) + " mins, "
                    if stay_time.seconds % 3600 >= 60
                    else ""
                )
                + (
                    str(stay_time.seconds % 3600 % 60) + " sec"
                    if stay_time.seconds % 3600 % 60
                    else ""
                )
            ),
            inline=False,
        )

        roles: typing.List[discord.Role] = member.roles[1:]
        log_embed.add_field(
            name="Roles",
            value=", ".join(role.mention for role in roles) or "None",
            inline=False,
        )

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        self.logger.info(color(f"user `{user}` banned", "red"))
        log_embed = self.log_embed(
            "delete",
            description=f"**User banned: {user.mention} ({user})**",
            footer=f"ID: {user.id}",
            user=user,
        )
        log_embed.set_thumbnail(url=user.avatar_url)

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        self.logger.info(color(f"user `{user}` unbanned", "green"))
        log_embed = self.log_embed(
            "create",
            description=f"**User unbanned: {user.mention} ({user})**",
            footer=f"ID: {user.id}",
            user=user,
        )
        log_embed.set_thumbnail(url=user.avatar_url)

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_embed = self.log_embed("edit", footer=f"ID: {before.id}", user=after)

        if before.nick != after.nick:
            self.logger.info(
                color(f"member `{after}` nickname changed: {before.nick} -> {after.nick}", "blue")
            )
            log_embed.description = f"**Nickname changed: {after.mention}**"
            log_embed.add_field(name="Before", value=before.nick, inline=False)
            log_embed.add_field(name="After", value=after.nick, inline=False)

        elif before.roles != after.roles:
            if len(before.roles) < len(after.roles):
                added: typing.List[discord.Role] = [
                    role for role in after.roles if role not in before.roles
                ]
                self.logger.info(
                    color(
                        f"member `{after}` roles added: {', '.join([r.name for r in added])}",
                        "green",
                    )
                )

                log_embed.description = (
                    f"**Role{'s' if len(added) > 1 else ''} added to {after.mention}:**"
                )
                log_embed.colour = discord.Colour.green()
                log_embed.add_field(
                    name="Added roles",
                    value=", ".join([role.mention for role in added]),
                    inline=False,
                )
            else:
                removed: typing.List[discord.Role] = [
                    role for role in before.roles if role not in after.roles
                ]
                self.logger.info(
                    color(
                        f"member `{after}` roles removed: {', '.join([r.name for r in removed])}",
                        "red",
                    )
                )

                log_embed.description = (
                    f"**Role{'s' if len(removed) > 1 else ''} removed from {after.mention}**"
                )
                log_embed.colour = discord.Colour.red()
                log_embed.add_field(
                    name="Removed roles",
                    value=", ".join([role.mention for role in removed]),
                    inline=False,
                )

        else:
            return

        await self.log_channel.send(embed=log_embed)

    @commands.Cog.listener()
    @log
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        log_embed = self.log_embed("edit", footer=f"ID: {member.id}", user=member)

        # Channel updates
        if before.channel is None and after.channel is not None:
            self.logger.info(color(f"member `{member}` joined vc: #{after.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** joined voice channel **{after.channel.mention}**"
            )

        elif before.channel is not None and after.channel is None:
            self.logger.info(color(f"member `{member}` left vc: #{before.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** left voice channel **{before.channel.mention}**"
            )
        elif before.channel != after.channel:
            self.logger.info(
                color(f"member `{member}` moved vc: #{before.channel} -> #{after.channel}", "blue")
            )
            log_embed.description = (
                f"Member **{member.mention}** moved from voice channel "
                f"**{before.channel.mention}** to **{after.channel.mention}**"
            )

        # Mute updates
        elif not before.mute and after.mute:
            self.logger.info(color(f"member `{member}` muted in vc: #{after.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** was muted in **{after.channel.mention}**"
            )

        elif before.mute and not after.mute:
            self.logger.info(color(f"member `{member}` unmuted in vc: #{after.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** was unmuted in **{after.channel.mention}**"
            )

        # Deaf updates
        elif not before.deaf and after.deaf:
            self.logger.info(color(f"member `{member}` deafened in vc: #{after.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** was deafened in **{after.channel.mention}**"
            )

        elif before.deaf and not after.deaf:
            self.logger.info(color(f"member `{member}` undeafened in vc: #{after.channel}", "blue"))
            log_embed.description = (
                f"Member **{member.mention}** was undeafened in **{after.channel.mention}**"
            )

        else:
            return

        await self.log_channel.send(embed=log_embed)
