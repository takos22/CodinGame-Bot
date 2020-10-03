from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Commands(bot=bot))


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def invite_link(self):
        return "https://discord.com/oauth2/authorize?client_id=759474863525330944&permissions=268528728&scope=bot"

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        embed = self.bot.embed(
            ctx=ctx,
            title="Invite me to your server",
            description=(
                f"[**Invite me here**]({self.invite_link})\n"
                f"Curently in {len(self.bot.guilds)} server{'s' * bool(len(self.bot.guilds) - 1)}."
            ),
        )
        await ctx.send(embed=embed)
