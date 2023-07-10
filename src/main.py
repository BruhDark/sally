import discord
from discord.commands import ApplicationContext
from discord.errors import DiscordException
from discord.ext import commands, tasks
from discord import utils

import dotenv
import os
import asyncio

from resources.database import database
from resources.views import ProcessTicketView

dotenv.load_dotenv()

intents = discord.Intents.all()

class Sally(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("sally "), intents=intents)
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
                    

    #async def on_application_command_error(self, ctx: ApplicationContext, exception: DiscordException):
    #     await ctx.respond(content=f"🛑 Ups! Algó salío mal. `{exception}`")
    #     raise exception

sally = Sally()
sally.activity, sally.status = discord.Game("The Eras Tour"), discord.Status.idle
sally.run(os.getenv("SALLY_TOKEN"))