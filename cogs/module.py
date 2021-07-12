import discord
from discord.ext import commands

import sphobjinv
import typing

if typing.TYPE_CHECKING:
    from bot import CodinGameBot


def setup(bot: "CodinGameBot"):
    bot.add_cog(Module(bot=bot))


class Module(commands.Cog):
    def __init__(self, bot):
        self.bot: "CodinGameBot" = bot

    # --------------------------------------------------------------------------
    # Helper methods

    def get_replied_reference(self, ctx: commands.Context):
        # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/context.py#L54
        ref = ctx.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    @property
    def module_name(self) -> str:
        return "codingame"

    @property
    def github_url(self) -> str:
        return f"https://github.com/takos22/{self.module_name}"

    @property
    def pypi_url(self) -> str:
        return f"https://pypi.org/project/{self.module_name}/"

    @property
    def docs_url(self) -> str:
        return f"https://{self.module_name}.readthedocs.io/en/latest/"

    @property
    def docs_inventory(self) -> sphobjinv.Inventory:
        return sphobjinv.Inventory(url=self.docs_url)

    # --------------------------------------------------------------------------
    # Commands

    @commands.command(aliases=["gh"])
    async def github(self, ctx: commands.Context):
        """Get the link to the GitHub of the module."""

        await ctx.send(
            self.github_url,
            reference=self.get_replied_reference(ctx),
        )

    @commands.command()
    async def pypi(self, ctx: commands.Context):
        """Get the link to the PyPI page of the module."""

        await ctx.send(
            self.pypi_url,
            reference=self.get_replied_reference(ctx),
        )

    @commands.command()
    async def docs(self, ctx: commands.Context, *, query: str = None):
        """Get the link to the docs."""

        if query is None:
            return await ctx.send(
                self.docs_url,
                reference=self.get_replied_reference(ctx),
            )

        inventory = self.docs_inventory
        best_matches = [
            inventory.objects[index]
            for _, index in inventory.suggest(query, with_index=True)
        ][:10]

        if not best_matches:
            return await ctx.send("No matches found.")

        description = "\n".join(
            [
                f"[`{obj.dispname_expanded[len(self.module_name):]}`]"
                f"({self.docs_url + obj.uri})"
                for obj in best_matches
            ]
        )
        embed = self.bot.embed(
            title=f"{self.module_name} docs best matches",
            description=description,
            ctx=ctx,
        )
        await ctx.send(
            embed=embed,
            reference=self.get_replied_reference(ctx),
        )
