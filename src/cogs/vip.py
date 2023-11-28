import aiohttp
import os
from discord.interactions import Interaction
from discord.ui.item import Item
import dotenv
import asyncio
from discord.ext import commands
import discord
import random
dotenv.load_dotenv()

words = ("INK", "GAYO", "ROBLOX", "SHOW", "POP",
         "MUSIC", "DRESS", "DANCE", "BEE", "CAT")

user_url = "https://users.roblox.com/v1/users/"
gamepass_url = 'https://apis.roblox.com'
api_key = os.getenv("ROBLOX_API_KEY")


class BuyVipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get VIP Role", custom_id="buyvipbutton")
    async def vip_role_button(self, button, interaction: discord.Interaction):
        await interaction.response.send_message(content="I have sent you a DM to continue with the process", ephemeral=True)

        await interaction.user.send(content="Please provide me your Roblox ID. You can find it in the URL of your profile. `Home > Profile > Numbers located at the top.`")

        def check(message: discord.Message):
            return message.author.id == interaction.user.id and message.guild == None and message.content.isdigit()

        try:
            user_id = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            return await interaction.user.send("This prompt timed out.")

        user_id = user_id.content

        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)
        await interaction.user.send(f"To confirm your identity, paste the following code in your account description: `{code}`. Say `done` when you finish.")
        await interaction.client.wait_for("message", check=code_check)

        url = user_url + user_id
        headers = {"x-api-key": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    await interaction.user.send("The ID you provided was invalid. Try again.")
                data = await response.json()
                description = data["description"]

        if code not in description:
            await interaction.user.send("Could not verify your identity. Try again.")
            return

        await interaction.user.send("Identity verified! Checking for gamepass and assigning roles.")
        g_url = gamepass_url + f'/cloud/v2/users/{user_id}/inventory-items'
        parameters = {"filter": "assetIds=664364469"}
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url, headers=headers, params=parameters) as response:
                resp = await response.json()
                if len(resp["inventoryItems"]) == 0:
                    await interaction.user.send("You do not own the gamepass. You must purchase first and then try again.")
                    return

        role = interaction.guild.get_role(1179032931457581107)
        await interaction.user.add_roles(role)
        await interaction.user.send("Your roles were given successfully.")

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        await interaction.user.send(f"Something went wrong. Send this to a staff member: `{error}`")


class Vip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(BuyVipView())

    @commands.slash_command(guild_ids=[881968885279117342])
    async def vip_sell(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):

        embed = discord.Embed(title="INKIGAYO VIP", description="tes test est")

        await channel.send(embed=embed, view=BuyVipView())


def setup(bot):
    bot.add_cog(Vip(bot))
