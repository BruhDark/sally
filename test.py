import discord
import asyncio
import dotenv
import os
from discord.ext import tasks

dotenv.load_dotenv()


bot = discord.Bot()
bot.queue: asyncio.Queue = None


@bot.event
async def on_ready():
    bot.add_view(QueueView())
    print("ready")


@bot.slash_command()
async def start_queue(ctx: discord.ApplicationContext, size: int):

    bot.queue: asyncio.Queue = asyncio.Queue(size)
    bot.queue_number = 0
    channel = bot.get_channel(987848591123034135)
    message = await channel.fetch_message(1126657381229666385)
    bot.queue_message = message

    await ctx.respond("Created queue")
    process_queue.start(bot.queue)


@bot.slash_command()
async def kill_queue(ctx):

    process_queue.cancel()
    bot.queue = None
    bot.queue_number = 0

    await ctx.respond("Killed queue")


@bot.slash_command()
async def send_queue_message(ctx: discord.ApplicationContext, channel: discord.TextChannel):

    view = QueueView()
    await channel.send(content="Join the queue to get a ticket! Processing number: 0", view=view)

    await ctx.respond("sent!")


class QueueView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join queue", custom_id="queuebutton")
    async def queue_callback(self, button: discord.ui.Button, interaction: discord.Interaction):

        if bot.queue is None:
            await interaction.response.send_message("There is no active queue!", ephemeral=True)
            return

        await interaction.response.send_message("Joining the queue...", ephemeral=True)

        if bot.queue.full():
            await interaction.edit_original_response(content="Queue is full! You will join the queue as soon as an space is available.\nDO NOT close this message OR click the button!")

        await bot.queue.put([bot.queue_number + 1, interaction.user])
        bot.queue_number += 1

        await interaction.edit_original_response(content=f"Joined queue! Your queue number is: {bot.queue_number}")


class ApproveView(discord.ui.View):
    def __init__(self, item_message, author):
        super().__init__(timeout=None)
        self.item_message: discord.Message = item_message
        self.author: discord.Member = author

    @discord.ui.button(label="Approve")
    async def approve_button(self, button, interaction):

        self.disable_all_items()
        await self.author.send("Your tickets got approved!")
        await interaction.response.send_message("Approved")

        self.stop()

    @discord.ui.button(label="Deny")
    async def deny_button(self, button, interaction):
        self.disable_all_items()
        await self.author.send("Your tickets were rejected.")
        await interaction.response.send_message("Denied")

        self.stop()


class SendModalView(discord.ui.View):
    def __init__(self, item_message):
        self.item_message = item_message
        super().__init__(timeout=15)

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(content="Your time to get tickets expired", view=self)

    @discord.ui.button(label="Get Ticket")
    async def ticket_callback(self, button, interaction):

        modal = UserModal(self.item_message)
        await interaction.response.send_modal(modal)

        await modal.wait()
        embed = discord.Embed()
        embed.add_field(name="Roblox usernames", value=modal.children[0].value)
        embed.add_field(name="discord usernames",
                        value=modal.children[1].value)

        view = ApproveView(self.item_message, interaction.user)
        await self.item_message.edit(embed=embed, view=view)
        if not await view.wait():
            self.stop()


class UserModal(discord.ui.Modal):
    def __init__(self, item_message, *args, **kwargs):
        super().__init__(title="Buy Tickets", timeout=None, *args, **kwargs)
        self.item_message: discord.Message = item_message

        self.add_item(discord.ui.InputText(
            label="Roblox usernames", placeholder="darkpxint, trigerism ...", style=discord.InputTextStyle.short))
        self.add_item(discord.ui.InputText(
            label="additional discord usernames", style=discord.InputTextStyle.short, required=False, value="None"))

    async def callback(self, interaction):

        await interaction.response.send_message("Your ticket request has been sent! You will receive a status reply in a few minutes.")
        self.stop()


@tasks.loop()
async def process_queue(queue: asyncio.Queue):
    channel = bot.get_channel(1126650801981497374)

    while True:
        try:
            await channel.send("Getting new item...")
            item = await asyncio.wait_for(queue.get(), 5)

        except asyncio.TimeoutError:
            await channel.send("Gave up waiting. On cooldown.")
            await bot.queue_message.edit(content=f"Join the queue to get a ticket! Processing number: Waiting")
            await asyncio.sleep(5)
            continue

        await bot.queue_message.edit(content=f"Join the queue to get a ticket! Processing number: {item[0]}")
        embed = discord.Embed(description="Waiting for user input...")
        message = await channel.send(content=f"Number: {item[0]}, Processing item: {item[1].id}", embed=embed)

        view = SendModalView(message)
        await item[1].send(content="It is your turn!", view=view)

        if await view.wait():
            await channel.send(f"USER TIMED OUT, Processed item number {item[0]}.")
            await message.edit(embed=discord.Embed(description="Timed out. No input received"))
            continue

        await channel.send(f"Processed item number {item[0]}.")

        queue.task_done()

bot.run(os.getenv("SALLY_TOKEN"))
