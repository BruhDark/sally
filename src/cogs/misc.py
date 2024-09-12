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
                    raise discord.ApplicationCommandError(
                        f"Failed to build RTFM cache for {target}"
                    )
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

    @commands.slash_command(description="Ask AI a prompt.", integration_types={discord.IntegrationType.user_install})
    @discord.option("prompt", description="The prompt to ask AI", max_lenght=400)
    @discord.option("hide", description="Hide the response", default=False)
    async def ask(self, ctx: discord.ApplicationContext, prompt: str, hide: bool):
        await ctx.defer(ephemeral=hide)
        messages = [{"role": "system", "content": "You are an AI assistant, you are part of a feature integration in a Discord bot where users can submit a command to ask you a question (prompt). Your answers should remain in a short or medium lenght almost all the time, there is nothing wrong with a large lenght answer, BUT, there is a limit of 2000 characters for messages, you should avoid hitting that limit, so your responses should be at max 1600 or 1700 characters because the final formatted response with your responses to prompts has aditional characters."}, {
            "role": "user", "content": prompt}]
        chat_completion = await self.groq_client.chat.completions.create(messages=messages, model="llama3-70b-8192", max_tokens=350)
        response = chat_completion.choices[0].message.content

        new_messages = messages + [{"role": "system", "content": response}]
        formatted_response = f"<:response:1283501616800075816> {response}\n-# <:prompt:1283501054079799419> Prompt: {prompt}"

        try:
            await ctx.respond(content=formatted_response, view=FollowConversation(self.groq_client, new_messages, hide), ephemeral=hide)
        except discord.HTTPException as e:
            await ctx.respond(content=f"<:error:1283509705376923648> The response the model returned was somehow too big or something went wrong. The response was saved to the chat completion, you can continue the conversation and ask it to make its last response shorter or start a new one.\n-# <:prompt:1283501054079799419> Prompt: {prompt}", view=FollowConversation(self.groq_client, new_messages, hide, "Make your last answer shorter"), ephemeral=hide)

    @ask.error
    async def ask_error(self, ctx: discord.ApplicationContext, error: commands.CommandError):
        error = getattr(error, "original", error)
        if isinstance(error, groq.APIConnectionError):
            return await ctx.respond(content=f"<:error:1283509705376923648> The server to generate the response could not be reached. Please try again in a few minutes.", ephemeral=True)

        elif isinstance(error, groq.RateLimitError):
            return await ctx.respond(content=f"<:error:1283509705376923648> You are being ratelimited! Slow down and try again in a few minutes.", ephemeral=True)

        elif isinstance(error, groq.APIStatusError):
            return await ctx.respond(content=f"<:error:1283509705376923648> The server to generate the response returned an error. Please try again.", ephemeral=True)

        else:
            await ctx.respond(content=f"<:error:1283509705376923648> Something went wrong while generating the response. Please try again.")
        raise error


def setup(bot):
    bot.add_cog(Misc(bot))
