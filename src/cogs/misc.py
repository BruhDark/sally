import aiohttp
import discord
from discord.ext import commands
from discord.utils import format_dt
from discord.interactions import Interaction
from discord.utils import as_chunks
from resources.rtfm import OVERRIDES, TARGETS, SphinxObjectFileReader, create_buttons, finder
from discord.ext.pages import Paginator
import groq
from groq import AsyncGroq
from resources.groq_views import FollowConversation


async def rtfm_autocomplete(ctx: discord.AutocompleteContext):
    assert isinstance(ctx.cog, Misc)
    results = await ctx.cog.get_rtfm_results(ctx.options["documentation"], ctx.value)
    return [key for key, _ in results] if results else []


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.rtfm_cache = {}
        self.bot.loop.create_task(self.build_docs())
        self.groq_client: AsyncGroq = AsyncGroq()

    async def build_docs(self) -> None:
        await self.bot.wait_until_ready()
        for target in TARGETS:
            self.bot.loop.create_task(self.build_documentation((target)))
        print("RTFM cache built")

    async def build_documentation(self, target: str) -> None:
        url = TARGETS[target]
        async with aiohttp.ClientSession() as session:
            async with session.get(OVERRIDES.get(target, url + "/objects.inv")) as req:
                if req.status != 200:
                    print(
                        f"WARNING: Failed to build RTFM cache for {target} due to {req.status}"
                    )
                    return
                self.rtfm_cache[target] = SphinxObjectFileReader(
                    await req.read()
                ).parse_object_inv(url)

    async def get_rtfm_results(self, target: str, query: str) -> list:
        if not (cached := self.rtfm_cache.get(target)):
            return []
        results = await finder(
            query,
            list(cached.items()),
            key=lambda x: x[0],
        )
        return results

    @commands.command()
    async def info(self, ctx: commands.Context):

        embed = discord.Embed(
            color=discord.Color.purple(), title="Information")
        embed.add_field(name="Latency", value=str(
            round(self.bot.latency * 1000)) + "ms")
        embed.add_field(name="Uptime", value=f"{format_dt(self.bot.uptime, "d")} {format_dt(self.bot.uptime, "T")} ({format_dt(self.bot.uptime, "R")})")

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

    @commands.slash_command(integration_types={discord.IntegrationType.user_install}, description="Search through documentations")
    @discord.option("documentation", description="The documentation to search in", choices=[*TARGETS.keys()])
    @discord.option("query", description="The query to search for", autocomplete=rtfm_autocomplete)
    @discord.option("hide", description="Hide the response", default=False)
    @discord.option("show_all", description="Show all results", default=False)
    async def rtfm(self, ctx: discord.ApplicationContext, documentation: str, query: str, hide: bool, show_all: bool):
        if not (results := await self.get_rtfm_results(documentation, query)):
            return await ctx.respond("Couldn't find any results", ephemeral=True)

        if not show_all:
            embed = discord.Embed(
                title=f"Searched in {documentation}",
                description=f"[`{results[0][0]}`]({results[0][1]})",
                color=discord.Color.blurple(),
            )
            return await ctx.respond(embed=embed, ephemeral=hide)

        if len(results) <= 15:
            embed = discord.Embed(
                title=f"Searched in {documentation}",
                description="\n".join(
                    [f"[`{key}`]({url})" for key, url in results]),
                color=discord.Color.blurple(),
            )
            return await ctx.respond(embed=embed, ephemeral=hide)

        chunks = as_chunks(iter(results), 15)
        embeds = [
            discord.Embed(
                title=f"Searched in {documentation}",
                description="\n".join(
                    [f"[`{key}`]({url})" for key, url in chunk]),
                color=discord.Color.blurple(),
            )
            for chunk in chunks
        ]

        paginator = Paginator(
            embeds,
            author_check=True,
            use_default_buttons=False,
            custom_buttons=create_buttons()
        )
        await paginator.respond(ctx.interaction, ephemeral=hide)


def setup(bot):
    bot.add_cog(Misc(bot))
