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
api_key = os.getenv("ROBLOX_API_KEY")


class BuyVipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="<:thunderbolt:987447657104560229>", label="Get VIP Role", style=discord.ButtonStyle.blurple, custom_id="buyvipbutton")
    async def vip_role_button(self, button, interaction: discord.Interaction):
        try:
            embed1 = discord.Embed(
                title=f":wave: Hello, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
            embed1.description = "Thank you for your interest on buying the VIP pass for INKIGAYO. If you haven't already, you must first purchase the VIP pass to continue with the process. [Click Here](https://www.roblox.com/game-pass/664364469/VIP) to buy it.\n\nNow, if you already purchased it, please provide me your **Roblox ID**. You can find it in the URL of your profile. `Home > Profile > Numbers located at the top in the URL.` Check the image if you don't know where it is."
            embed1.set_image(url="https://dark.hates-this.place/i/gzEw6M.png")
            embed1.set_footer(text="This prompt will expire in 10 minutes",
                              icon_url=interaction.guild.icon.url)
            await interaction.user.send(embed=embed1)
            await interaction.response.send_message(content="<:box:987447660510334976> I DM'ed you. We will continue the process there.", ephemeral=True)
        except:
            await interaction.response.send_message(content="<:x_:1174507495914471464> Please open your DMs and try again!")

        def check(message: discord.Message):
            return message.author.id == interaction.user.id and message.guild == None and message.content.isdigit()

        try:
            user_id = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            return await interaction.user.send("<:x_:1174507495914471464> Your prompt timed out.")

        user_id = user_id.content

        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=discord.Color.nitro_pink())
        embed2.description = f"Thank you! We will need to confirm you indeed own this account, please navigate to [your profile](https://roblox.com/users/{user_id}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done."
        embed2.add_field(
            name="<:editing:1174508480481218580> Code", value=str(code))

        await interaction.user.send(embed=embed2)
        await interaction.client.wait_for("message", check=code_check)

        url = user_url + user_id
        headers = {"x-api-key": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()))
                data = await response.json()
                description = data["description"]

        if code not in description:
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Couldn't find the code in your profile. Please try again.", color=discord.Color.red()))
            return

        await interaction.user.send(embed=discord.Embed(description="<:checked:1173356058387951626> Identity confirmed! Checking if you own the gamepass and assigning you the role.", color=discord.Color.green()))
        g_url = f"https://inventory.roblox.com/v1/users/{user_id}/items/1/664364469/is-owned"
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url, headers=headers) as response:
                resp = await response.json()
                if not resp:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> You do not own the gamepass, you **must** buy the gamepass before trying to claim the role. Please try again.", color=discord.Color.red()))
                    return

        role = interaction.guild.get_role(1179032931457581107)
        await interaction.user.add_roles(role)
        embed3 = discord.Embed(
            title=f"<:owner:881973891017355344> Welcome to the VIP team of INKIGAYO, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
        embed3.description = "I have assigned your roles and you are not part of the VIP users of INKIGAYO! Enjoy these benefits for all of our shows and thank you for supporting us!\n\nIf you do not see the VIP role in your server profile, please contact a staff member."
        await interaction.user.send(embed=embed3)

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        await interaction.user.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=discord.Color.red()))
        raise error


class Vip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(BuyVipView())

    @commands.slash_command(guild_ids=[881968885279117342, 1170821546038800464])
    async def vip_sell(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):

        embed = discord.Embed(
            title="<:thunderbolt:987447657104560229> INKIGAYO VIP", color=discord.Color.nitro_pink())
        embed.description = "Want to enjoy awesome benefits for all of our INKIGAYO shows? Buy the VIP gamepass to earn them! Join the VIP people and enjoy these benefits:"
        embed.description += "\n\n<:rightarrow:1173350998388002888> **Front line** seats."
        embed.description += "\n<:rightarrow:1173350998388002888> Join **15 minutes before** everyone else."
        embed.description += "\n<:rightarrow:1173350998388002888> **Priority queue**, first in line to join the studio."
        embed.description += "\n<:rightarrow:1173350998388002888> **Meet** your favorite **idols** in the backstage after the show!"

        embed.description += "\n\nBuy the VIP gamepass on the link below, then click the button to earn your gamepass. (Your identity will be confirmed and then we will check if you own the gamepass)"
        embed.add_field(name="<:link:986648044525199390> Become a VIP",
                        value="[Click Here](https://www.roblox.com/game-pass/664364469/VIP)")
        await channel.send(embed=embed, view=BuyVipView())


def setup(bot):
    bot.add_cog(Vip(bot))
