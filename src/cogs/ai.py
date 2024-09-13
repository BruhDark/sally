import discord
from discord.ext import commands
import groq
from groq import AsyncGroq
from resources.groq_views import FollowConversation, DestroyConversation
import asyncio


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.groq = AsyncGroq()
        self.bot.ai_conversations = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if str(message.channel.id) in self.bot.ai_conversations.keys():
            await message.add_reaction("<:thinking:1283958575571538020>")

            messages = self.bot.ai_conversations[str(
                message.channel.id)]["messages"]
            messages.append({"role": "user", "name": message.author.global_name,
                            "content": f"[{message.author.global_name}] " + message.content})

            try:
                chat_completion = await self.groq.chat.completions.create(messages=messages, model="llama3-70b-8192", max_tokens=400)

            except groq.RateLimitError:
                re = await message.reply(content=f"<:error:1283509705376923648> We are being ratelimited! Slow down and continue the conversation in a few minutes. Applying a 5 minutes cooldown to this conversation.")
                await re.add_reaction("<:cooldown:1283965653048627291>")
                await asyncio.sleep(60 * 5)
                await re.remove_reaction("<:cooldown:1283965653048627291>", message.guild.me)
                return

            except Exception as e:
                await message.reply(content=f"<:error:1283509705376923648> Failed to generate a response! Please try again in a few minutes.")
                raise e

            response = chat_completion.choices[0].message.content

            new_messages = messages + [{"role": "system", "content": response}]
            jump_url = self.bot.ai_conversations[str(
                message.channel.id)]["original_message_url"]
            formatted_response = f"<:response:1283501616800075816> {response}\n-# <:sad:1283952161109049355> [Stop conversation]({jump_url}) - Live conversation ({len(messages)} total messages)"

            try:
                await message.reply(content=formatted_response, mention_author=False)
            except discord.HTTPException as e:
                await message.channel.send(content=f"<:error:1283509705376923648> The response the model returned was somehow too big or something went wrong. The response was saved to the chat completion, you can continue the conversation and ask it to make its last response shorter or start a new one.\n -# <:sad:1283952161109049355> [Stop conversation]({jump_url}) - Live conversation ({len(messages)} total messages)")

            await message.remove_reaction("<:thinking:1283958575571538020>", message.guild.me)
            self.bot.ai_conversations[str(
                message.channel.id)]["messages"] = new_messages

    @commands.slash_command(name="chat", description="Begin a chat with AI in this channel.", integration_types={discord.IntegrationType.guild_install})
    @ discord.option("behaviour", description="A small description of how you want AI to behave. eg. 'You are a famous singer and we are fans.'", max_lenght=200, default=None)
    async def chat_ai(self, ctx: discord.ApplicationContext, behaviour: str = None):
        ai_context = "Your name is Sally. You are an AI assistant in a Discord channel. Multiple users can talk to you at the same time, the name of the users will be displayed in the content inside square brackets before what the user typed, for example: '[John] Who is Taylor Swift?', this is for you to know who is speaking to you if multiple users are interacting, You DO NOT add these square brackets or your name to your responses. If you are using a user's name, you DO NOT add the square brackets to the response. You only use the. Your response should remain in a short or medium lenght almost all the time, there is nothing wrong with a large lenght answer, BUT, there is a limit of 2000 characters for messages, you should avoid hitting that limit, so your responses should be at max 1800 characters because the final formatted response with your responses to prompts has aditional characters."
        if behaviour:
            ai_context += " Here is aditional behaviour for you to follow on this conversation: " + behaviour

        messages = [{"role": "system", "content": ai_context}]
        self.bot.ai_conversations[str(ctx.channel.id)] = {
            "messages": messages, "original_message_url": None}

        await ctx.respond(content=f"<:prompt:1283501054079799419> You started an AI chat on this channel! Send any initial message for AI to respond. Any user who sends a message in this channel will be considered as a user talking to AI.\n-# <:notalking:1283950338193489930> You can stop the conversation at any time using the button below.", view=DestroyConversation(str(ctx.channel.id)))
        or_response = await ctx.interaction.original_response()
        self.bot.ai_conversations[str(
            ctx.channel.id)]["original_message_url"] = or_response.jump_url

    @ commands.slash_command(description="Ask AI a prompt.", integration_types={discord.IntegrationType.user_install})
    @ discord.option("prompt", description="The prompt to ask AI", max_lenght=400)
    @ discord.option("hide", description="Hide the response", default=False)
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

    @ ask.error
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


def setup(bot: commands.Bot):
    bot.add_cog(AICog(bot))
