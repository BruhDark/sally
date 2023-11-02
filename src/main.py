import discord
from discord.commands import ApplicationContext
from discord.errors import DiscordException
from discord.ext import commands

import dotenv
import os
import asyncio
from threading import Thread
from flask import Flask

from resources.database import database

dotenv.load_dotenv()

app = Flask('')


@app.route('/')
def main():
  return "Your Bot Is Ready"


def run():
  app.run(host="0.0.0.0", port=8000)


def keep_alive():
  server = Thread(target=run)
  server.start()


intents = discord.Intents.all()


class Sally(commands.Bot):

  def __init__(self):
    super().__init__(command_prefix=commands.when_mentioned_or("sally!"),
                     intents=intents)
    self.database = database
    self.queue: asyncio.Queue = None
    self.queue_paused = False

    for cog in os.listdir("src/cogs"):
      if cog.endswith(".py"):
        try:
          self.load_extension(f"cogs.{cog[:-3]}", store=False)
          print(f"✅ Loaded cog: {cog}")
        except Exception as e:
          print(f"❌ Failed to load cog: {cog}: {e}")
          raise e

  async def on_application_command_error(self, ctx: ApplicationContext, exception: DiscordException):
    if isinstance(exception, commands.CheckFailure):
      await ctx.respond(embed=discord.Embed(description=f"🛑 {exception}", color=discord.Color.red()))
      return
                               
    await ctx.respond(embed=discord.Embed(description=f"🛑 Ups! Algó salío mal.\n```py\n{exception}```", color=discord.Color.red()))
    raise exception

  async def on_ready(self):
    keep_alive()


sally = Sally()
sally.activity, sally.status = discord.Game(
  "The Eras Tour"), discord.Status.idle
sally.run(os.getenv("SALLY_TOKEN"))
