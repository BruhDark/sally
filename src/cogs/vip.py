import aiohttp
import os
from discord.interactions import Interaction
from discord.ui.item import Item
import dotenv
import asyncio
from discord.ext import commands
import discord
import random

from resources.database import get_roblox_info

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
        await interaction.response.defer(ephemeral=True)
        roblox_data = await get_roblox_info(interaction.user.id)
        if not roblox_data:
            return await interaction.followup.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> You are not verified with Sally! Use `/verify` in a channel to verify.", color=discord.Color.red()), ephemeral=True)

        user_id = roblox_data["roblox_id"]
        # 664364469
        g_url = f"https://inventory.roblox.com/v1/users/{user_id}/items/1/664364469/is-owned"
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url) as response:
                resp = await response.json()
                if not resp:
                    await interaction.followup.send(embed=discord.Embed(description="<:x_:1174507495914471464> You do not own the gamepass, you **must** buy the gamepass before trying to claim the role.", color=discord.Color.red()), ephemeral=True)
                    return

        vip_role = interaction.guild.get_role(1179032931457581107)
        await interaction.user.add_roles(vip_role, reason=f"Bought VIP for Roblox account: {user_id}")
        embed3 = discord.Embed(
            title=f"<:thunderbolt:987447657104560229> Welcome to the VIP team of INKIGAYO, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
        embed3.description = "I have assigned your roles and you are now part of the VIP users of **INKIGAYO**! Enjoy these benefits for **all** of our shows and thank you for supporting us!\n\n<:lifesaver:986648046592983150> If you do not see the VIP role in your server profile, please contact a staff member."
        await interaction.followup.send(embed=embed3, ephemeral=True)

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        await interaction.followup.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=discord.Color.red()), ephemeral=True)
        raise error


class Vip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(BuyVipView())

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild.id != 1170821546038800464:
            return
        vip_role = after.guild.get_role(1179032931457581107)
        booster_role = after.guild.get_role(1177467255802564698)
        if booster_role in after.roles and booster_role not in before.roles:
            await after.add_roles(vip_role, "User is a server booster.")

        elif booster_role not in after.roles and booster_role in before.roles:
            await after.remove_roles(vip_role, "User is no longer a server booster.")

    @commands.command(name="vipsell")
    @commands.is_owner()
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
