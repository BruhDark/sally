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


class TryAgain(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60*5, disable_on_timeout=True)

    @discord.ui.button(label="Try Again", style=discord.ButtonStyle.blurple, emoji="<:reload:1179444707114352723>")
    async def try_again(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

        embed1 = discord.Embed(
            title=f":wave: Hello, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
        embed1.description = "Thank you for your interest on buying the VIP pass for INKIGAYO. If you haven't already, you must first purchase the VIP pass to continue with the process. [Click Here](https://www.roblox.com/game-pass/664364469/VIP) to buy it.\n\nNow, if you already purchased it, please provide me your **Roblox ID**. You can find it in the URL of your profile. `Home > Profile > Numbers located at the top in the URL.` Check the image if you don't know where it is."
        embed1.set_image(url="https://dark.hates-this.place/i/gzEw6M.png")
        embed1.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=interaction.client.user.display_avatar.url)
        await interaction.followup.send(embed=embed1)

        def check(message: discord.Message):
            if message.author.id == interaction.user.id and message.guild == None:
                if not message.content.isdigit():
                    asyncio.run_coroutine_threadsafe(message.channel.send(
                        content="<:x_:1174507495914471464> You are not providing a valid ID. You only provide the **numbers** located in the URL."), interaction.client.loop)
                    return False
                return True
            return False

        try:
            user_id = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            return await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Your prompt timed out.", color=discord.Color.red()), view=TryAgain())

        user_id = user_id.content

        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=discord.Color.nitro_pink())
        embed2.description = f"Thank you! We will need to confirm you indeed own this account, please navigate to [your profile](https://roblox.com/users/{user_id}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done, if you don't reply in 10 minutes, I will automatically check."
        embed2.add_field(
            name="<:editing:1174508480481218580> Code", value=str(code))
        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=interaction.client.user.display_avatar.url)

        await interaction.user.send(embed=embed2)
        try:
            await interaction.client.wait_for("message", check=code_check, timeout=60*10)
        except asyncio.TimeoutError:
            pass

        url = user_url + user_id
        headers = {"x-api-key": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()), view=TryAgain())
                data = await response.json()
                description = data["description"]

        if code not in description:
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Couldn't find the code in your profile. Please try again.", color=discord.Color.red()), view=TryAgain())
            return

        await interaction.user.send(embed=discord.Embed(description="<:checked:1173356058387951626> Identity confirmed! Checking if you own the gamepass and assigning you the role.", color=discord.Color.green()))
        # 664364469
        g_url = f"https://inventory.roblox.com/v1/users/{user_id}/items/1/664364469/is-owned"
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url, headers=headers) as response:
                resp = await response.json()
                if not resp:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> You do not own the gamepass, you **must** buy the gamepass before trying to claim the role. Please try again.", color=discord.Color.red()), view=TryAgain())
                    return

        guild = interaction.client.get_guild(1170821546038800464)
        role = guild.get_role(1179032931457581107)
        await interaction.user.add_roles(role)
        embed3 = discord.Embed(
            title=f"<:thunderbolt:987447657104560229> Welcome to the VIP team of INKIGAYO, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
        embed3.description = "I have assigned your roles and you are now part of the VIP users of **INKIGAYO**! Enjoy these benefits for **all** of our shows and thank you for supporting us!\n\n<:lifesaver:986648046592983150> If you do not see the VIP role in your server profile, please contact a staff member."
        await interaction.user.send(embed=embed3)

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        await interaction.user.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=discord.Color.red()))
        raise error


class BuyVipView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="<:thunderbolt:987447657104560229>", label="Get VIP Role", style=discord.ButtonStyle.blurple, custom_id="buyvipbutton")
    async def vip_role_button(self, button, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            embed1 = discord.Embed(
                title=f":wave: Hello, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
            embed1.description = "Thank you for your interest on buying the VIP pass for INKIGAYO. If you haven't already, you must first purchase the VIP pass to continue with the process. [Click Here](https://www.roblox.com/game-pass/664364469/VIP) to buy it.\n\nNow, if you already purchased it, please provide me your **Roblox ID**. You can find it in the URL of your profile. `Home > Profile > Numbers located at the top in the URL.` Check the image if you don't know where it is."
            embed1.set_image(url="https://dark.hates-this.place/i/gzEw6M.png")
            embed1.set_footer(text="This prompt will expire in 10 minutes",
                              icon_url=interaction.guild.icon.url)
            await interaction.user.send(embed=embed1)
            await interaction.followup.send(embed=discord.Embed(description="<:box:987447660510334976> I have sent you a private message! We will continue the process there.", color=discord.Color.nitro_pink()), ephemeral=True)
        except:
            await interaction.followup.send(embed=discord.Embed(description="<:x_:1174507495914471464> Please open your DMs and try again!", color=discord.Color.red()), ephemeral=True)

        def check(message: discord.Message):
            if message.author.id == interaction.user.id and message.guild == None:
                if not message.content.isdigit():
                    asyncio.run_coroutine_threadsafe(message.channel.send(
                        content="<:x_:1174507495914471464> You are not providing a valid ID. You only provide the **numbers** located in the URL."), interaction.client.loop)
                    return False
                return True
            return False

        try:
            user_id = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            return await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Your prompt timed out.", color=discord.Color.red()), view=TryAgain())

        user_id = user_id.content

        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=discord.Color.nitro_pink())
        embed2.description = f"Thank you! We will need to confirm you indeed own this account, please navigate to [your profile](https://roblox.com/users/{user_id}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done, if you don't reply in 10 minutes, I will automatically check."
        embed2.add_field(
            name="<:editing:1174508480481218580> Code", value=str(code))

        await interaction.user.send(embed=embed2)
        try:
            await interaction.client.wait_for("message", check=code_check, timeout=60*10)
        except asyncio.TimeoutError:
            pass

        url = user_url + user_id
        headers = {"x-api-key": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()), view=TryAgain())
                data = await response.json()
                description = data["description"]

        if code not in description:
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Couldn't find the code in your profile. Please try again.", color=discord.Color.red()), view=TryAgain())
            return

        await interaction.user.send(embed=discord.Embed(description="<:checked:1173356058387951626> Identity confirmed! Checking if you own the gamepass and assigning you the role.", color=discord.Color.green()))
        # 664364469
        g_url = f"https://inventory.roblox.com/v1/users/{user_id}/items/1/664364469/is-owned"
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url, headers=headers) as response:
                resp = await response.json()
                if not resp:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> You do not own the gamepass, you **must** buy the gamepass before trying to claim the role. Please try again.", color=discord.Color.red()), view=TryAgain())
                    return

        role = interaction.guild.get_role(1179032931457581107)
        await interaction.user.add_roles(role)
        embed3 = discord.Embed(
            title=f"<:thunderbolt:987447657104560229> Welcome to the VIP team of INKIGAYO, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
        embed3.description = "I have assigned your roles and you are now part of the VIP users of **INKIGAYO**! Enjoy these benefits for **all** of our shows and thank you for supporting us!\n\n<:lifesaver:986648046592983150> If you do not see the VIP role in your server profile, please contact a staff member."
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
        embed.description = "Want to enjoy **amazing benefits** for all of our **INKIGAYO** shows? Buy the **VIP gamepass** to earn them! Join the VIP people and enjoy these benefits:"
        embed.description += "\n\n<:rightarrow:1173350998388002888> **Front line** seats."
        embed.description += "\n<:rightarrow:1173350998388002888> Join **15 minutes before** everyone else."
        embed.description += "\n<:rightarrow:1173350998388002888> **Priority queue**, first in line to join the studio."
        embed.description += "\n<:rightarrow:1173350998388002888> **Meet** your favorite **idols** in the backstage after the show!"

        embed.description += "\n\nBuy the **VIP gamepass** on the link below, then click the button to earn your VIP role in the server. (Your identity will be confirmed and then we will check if you own the gamepass)"
        embed.add_field(name="<:link:986648044525199390> Become a VIP",
                        value="[Click Here](https://www.roblox.com/game-pass/664364469/VIP)")
        await channel.send(embed=embed, view=BuyVipView())


def setup(bot):
    bot.add_cog(Vip(bot))
