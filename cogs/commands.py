import discord
from discord.ext import commands

import asyncio
import typing

from utils import color

if typing.TYPE_CHECKING:
    from bot import CodinGameBot


def setup(bot: "CodinGameBot"):
    bot.add_cog(Commands(bot=bot))


class Commands(commands.Cog):
    """General bot commands."""

    def __init__(self, bot):
        self.bot: "CodinGameBot" = bot
        self.logger = self.bot.logger.getChild("commands")

    # --------------------------------------------------------------------------
    # Helper methods

    @property
    def invite_link(self):
        return (
            "https://discord.com/oauth2/authorize?client_id=759474863525330944&"
            "permissions=268528720&scope=bot"
        )

    # --------------------------------------------------------------------------
    # Commands

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logout(
        self,
        ctx: commands.Context,
        seconds_before_logout: int = 0,
    ):
        """Logout the bot"""

        await asyncio.sleep(seconds_before_logout)
        self.logger.warning(color("logging out", "red"))
        await ctx.send("**Logging out...**")
        try:
            await self.bot.logout()
        except Exception as error:
            embed = self.bot.embed(
                ctx=ctx, title="Logout failed", color=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            await self.bot.handle_error(error, ctx=ctx)

    @commands.command(aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check the bot latency"""

        await ctx.send(f"Pong! `{int(self.bot.latency*1000)}ms`")

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Get the bot invite link"""

        embed = self.bot.embed(
            ctx=ctx,
            title="Invite me to your server",
            description=(
                f"[**Invite me here**]({self.invite_link})\n"
                f"Curently in {len(self.bot.guilds)} "
                f"server{'s' * bool(len(self.bot.guilds) - 1)}."
            ),
        )
        await ctx.send(embed=embed)
