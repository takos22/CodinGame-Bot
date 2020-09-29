import discord
from discord import colour
from discord.ext import commands
import aiocodingame


def setup(bot: commands.Bot):
    bot.add_cog(CodinGame(bot=bot))


class CodinGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start(self):
        self.client = aiocodingame.Client()

    async def close(self):
        await self.client.close()

    @staticmethod
    def clean(name: str):
        return (
            name.replace("_", "\\_")
            .replace("*", "\\*")
            .replace("`", "`\u200b")
            .replace("@", "\\@")
            .replace("@everyone", "@\u200beveryone")
        )

    @commands.group(name="codingame", aliases=["cg"])
    async def codingame(self, ctx: commands.Context):
        """Commands for the CodinGame API."""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(self.bot.get_command("codingame"))

    @codingame.command(name="codingamer", aliases=["user", "c"])
    async def codingamer(self, ctx: commands.Context, public_handle: str):
        """Get a Codingamer from his public handle."""
        try:
            codingamer: aiocodingame.CodinGamer = await self.client.get_codingamer(public_handle)
        except (ValueError, aiocodingame.CodinGamerNotFound) as error:
            return await ctx.send(self.clean(str(error)))
        else:
            embed = self.bot.embed(
                ctx,
                title=f"**Codingamer:** {self.clean(codingamer.pseudo or codingamer.public_handle)}",
                description=self.clean(f"{codingamer.tagline or ''}\n{codingamer.biography or ''}"),
            )

            if codingamer.avatar:
                embed.set_thumbnail(url=codingamer.avatar_url)

            embed.set_author(name=f"{codingamer.public_handle} | {codingamer.id}")

            embed.add_field(name="Rank", value=codingamer.rank)
            embed.add_field(name="Level", value=codingamer.level)
            embed.add_field(name="Country", value=codingamer.country_id)

            if codingamer.category:
                embed.add_field(name="Category", value=codingamer.category.title())
            if codingamer.school:
                embed.add_field(name="School", value=codingamer.school)
            if codingamer.company:
                embed.add_field(name="Company", value=codingamer.company)

            await ctx.send(embed=embed)

    @codingame.command(name="clash_of_code", aliases=["clash", "coc"])
    async def clash_of_code(self, ctx: commands.Context, public_handle: str):
        """Get a Clash of Code from its public handle."""
        try:
            clash_of_code: aiocodingame.ClashOfCode = await self.client.get_clash_of_code(public_handle)
        except (ValueError, aiocodingame.ClashOfCodeNotFound) as error:
            return await ctx.send(self.clean(str(error)))
        else:
            embed = self.bot.embed(
                ctx,
                title=f"**Clash of Code:** {clash_of_code.public_handle}",
                description=f"**[Join here]({clash_of_code.join_url})**",
            )

            embed.add_field(name="Public", value=clash_of_code.public)
            embed.add_field(name="Min players", value=clash_of_code.min_players)
            embed.add_field(name="Max players", value=clash_of_code.max_players)
            embed.add_field(name="Possible modes", value=", ".join(clash_of_code.modes) or "Any")
            embed.add_field(name="Programming languages", value=", ".join(clash_of_code.programming_languages) or "All")
            embed.add_field(name="Started", value=clash_of_code.started)
            embed.add_field(name="Finished", value=clash_of_code.finished)

            if clash_of_code.started:
                embed.add_field(name="Mode", value=clash_of_code.mode)

            embed.add_field(
                name="Players", value=", ".join(self.clean(player.pseudo) for player in clash_of_code.players)
            )
            await ctx.send(embed=embed)

    @codingame.command(name="pending_clash_of_code", aliases=["pending", "pcoc"])
    async def pending_clash_of_code(self, ctx: commands.Context):
        """Get a pending public Clash of Code."""
        clash_of_code: aiocodingame.ClashOfCode = await self.client.get_pending_clash_of_code()

        if clash_of_code is None:
            return await ctx.send("No pending clashes currently, try again later.")

        embed = self.bot.embed(
            ctx,
            title=f"**Clash of Code:** {clash_of_code.public_handle}",
            description=f"**[Join here]({clash_of_code.join_url})**",
        )

        embed.add_field(name="Public", value=clash_of_code.public)
        embed.add_field(name="Min players", value=clash_of_code.min_players)
        embed.add_field(name="Max players", value=clash_of_code.max_players)
        embed.add_field(
            name="Possible modes",
            value=", ".join(clash_of_code.modes)
            if clash_of_code.modes is not None else "Any"
        )
        embed.add_field(
            name="Programming languages",
            value=", ".join(clash_of_code.programming_languages)
            if clash_of_code.programming_languages is not None
            else "All",
        )
        embed.add_field(name="Started", value=clash_of_code.started)
        embed.add_field(name="Finished", value=clash_of_code.finished)

        if clash_of_code.started:
            embed.add_field(name="Mode", value=clash_of_code.mode)

        embed.add_field(name="Players", value=", ".join(self.clean(player.pseudo) for player in clash_of_code.players))
        await ctx.send(embed=embed)