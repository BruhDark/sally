import discord
from discord.ext import commands
import aiohttp
import os
import dotenv
import traceback
from datetime import datetime

dotenv.load_dotenv()
url = os.getenv("WEBHOOK_URL")
roblox_log_url = os.getenv("ROBLOX_LOG_WEBHOOK_URL")


async def send_join_log(embed: discord.Embed):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(roblox_log_url, session=session)
        await webhook.send(embed=embed)


async def send_command_error(ctx: commands.Context | discord.ApplicationContext, error: Exception):
    async with aiohttp.ClientSession() as session:

        webhook = discord.Webhook.from_url(url, session=session)
        tb = ''.join(traceback.format_exception(
            error, error, error.__traceback__))
        tb = tb + "\n"

        embed = discord.Embed(
            title=f"<:x_:1174507495914471464> Something went wrong", color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.description = f"```py\n{tb}```"

        embed.add_field(name="Author", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(
            name="Command", value=f"{ctx.command.qualified_name}")
        embed.add_field(
            name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})")

        await webhook.send(embed=embed)
