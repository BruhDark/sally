import discord
from discord.ext import commands
from discord.utils import format_dt
from discord.interactions import Interaction


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx: commands.Context):

        embed = discord.Embed(
            color=discord.Color.purple(), title="Information")
        embed.add_field(name="Latency", value=str(
            round(self.bot.latency * 1000)) + "ms")
        embed.add_field(name="Uptime", value=format_dt(self.bot.uptime, "R"))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.is_owner()
    async def say(self, ctx: discord.ApplicationContext, *, text: str):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            return

        message = ctx.message.reference.message_id if ctx.message.reference is not None else None
        message = self.bot.get_message(
            message) if message is not None else None

        await message.reply(text) if message is not None else await ctx.send(text)


def setup(bot):
    bot.add_cog(Misc(bot))
