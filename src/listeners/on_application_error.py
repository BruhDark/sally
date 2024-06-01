import discord
from discord.ext import commands
from resources import webhook_manager
import os
import aiohttp
import traceback
import datetime
import sys


class OnApplicationCommandError(commands.Cog):
    @commands.Cog.listener("on_application_command_error")
    async def on_application_command_error(self, ctx, error):
        base_embed = discord.Embed(color=discord.Color.red())
        base_embed.description = "<:x_:1174507495914471464> "

        if isinstance(error, commands.NoPrivateMessage):
            base_embed.description += "You can only use this command in a server."

        elif isinstance(error, commands.MissingPermissions):
            base_embed.description += f"I am missing the following permissions: `{', '.join(error.missing_permissions)}`"

        elif isinstance(error, commands.CheckFailure):
            base_embed.description += str(error)

        elif isinstance(error, commands.NotOwner):
            base_embed.description += "You are not allowed to use this command."

        else:
            base_embed.description += f"Something went wrong.\n\n```py\n{error}\n```"
            await webhook_manager.send_command_error(ctx, error)

        await ctx.respond(embed=base_embed)

    @commands.Cog.listener()
    async def on_error(self, event):
        async with aiohttp.ClientSession() as session:
            url = os.getenv("WEBHOOK_URL")
            webhook = discord.Webhook.from_url(url, session=session)
            tb = ''.join(traceback.format_tb(sys.exc_info()[2]))
            tb = tb + "\n" + str(sys.exc_info()[1])

            embed = discord.Embed(
                title=f"Something Went Wrong | Event: {event}", color=discord.Color.red(),
                timestamp=datetime.utcnow())
            embed.description = f"```py\n{tb}```"
            await webhook.send(embed=embed)


def setup(bot):
    bot.add_cog(OnApplicationCommandError())
