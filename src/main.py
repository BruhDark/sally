import discord
import datetime
from discord.ext import commands

import dotenv
import os
import asyncio

from resources.database import database
from resources import webhook_manager

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class Sally(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("s!"),
                         intents=intents)
        self.database = database
        self.queue: asyncio.Queue = None
        self.queue_paused = False
        self.user_prompts = []
        self.pending_verifications = {}
        self.ready_fired = False

        for cog in os.listdir("src/cogs"):
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{cog[:-3]}", store=False)
                    print(f"✅ Loaded cog: {cog}")
                except Exception as e:
                    print(f"❌ Failed to load cog: {cog}: {e}")
                    raise e

        for cog in os.listdir("src/listeners"):
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"listeners.{cog[:-3]}", store=False)
                    print(f"✅ Loaded listener: {cog}")
                except Exception as e:
                    print(f"❌ Failed to load listener: {cog}: {e}")
                    raise e

    async def on_ready(self):
        if not self.ready_fired:
            print("Ready!")
            self.ready_fired = True
            self.uptime = datetime.datetime.now()


sally = Sally()
sally.status = discord.Status.idle
sally.activity = discord.Activity(
    type=discord.ActivityType.watching, name="the WePeak members")

if __name__ == "__main__":
    sally.run(os.getenv("SALLY_TOKEN"))
