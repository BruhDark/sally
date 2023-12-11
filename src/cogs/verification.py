import discord
from discord.ext import commands
from discord.interactions import Interaction
from resources.database import add_roblox_info, get_roblox_info, delete_roblox_info, blacklist_roblox_user, remove_blacklist_roblox
import asyncio
import aiohttp
import random
import os

words = ("INK", "GAYO", "ROBLOX", "SHOW", "POP",
         "MUSIC", "DRESS", "DANCE", "BEE", "CAT")

ROBLOX_USERS_ENDPOINT = "https://users.roblox.com/v1/users/"
ROBLOX_USERNAMES_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
api_key = os.getenv("ROBLOX_API_KEY")


class VerifyView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(disable_on_timeout=True)
        self.author = author

    async def validate_username(self, username: str):
        data = {"usernames": [username], "excludeBannedUsers": True}
        headers = {"accept": "application/json", "Content-Type": "text/json"}
        print(data)
        async with aiohttp.ClientSession() as session:
            async with session.post(ROBLOX_USERNAMES_ENDPOINT, data=data, headers=headers) as resp:
                response = await resp.json()
                print(response)
                if len(response["data"]) == 0:
                    return False, None

                return True, response["data"][0]["id"]

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(content="This button is not for you!", ephemeral=True)
        return False

    @discord.ui.button(emoji="<:link:986648044525199390>", label="Verify Roblox account")
    async def verify_button(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        try:
            embed1 = discord.Embed(
                title=f":wave: Hello, {interaction.user.display_name}!", color=discord.Color.nitro_pink())
            embed1.description = "Welcome to the verification process to link your Roblox account with Sally! This will only take five minutes.\nPlease provide me your **Roblox ID**. You can find it in the link of your profile, on the Roblox web. `Home > Profile > Numbers located at the top in the URL.` Check the image if you don't know where it is."
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
            roblox_id = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            return await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Your prompt timed out.", color=discord.Color.red()))

        roblox_id = roblox_id.content

        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=discord.Color.nitro_pink())
        embed2.description = f"Thank you! We will need to confirm you indeed own this account, please navigate to [your profile](https://roblox.com/users/{roblox_id}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done, if you don't reply in 10 minutes, I will automatically check."
        embed2.add_field(
            name="<:editing:1174508480481218580> Code", value=str(code))

        await interaction.user.send(embed=embed2)
        try:
            await interaction.client.wait_for("message", check=code_check, timeout=60*10)
        except asyncio.TimeoutError:
            pass

        url = ROBLOX_USERS_ENDPOINT + roblox_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()))
                    return
                data = await response.json()
                description = data["description"]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={data['id']}&size=420x420&format=Png&isCircular=false") as resp:
                response = await resp.json()
                print(response)
                avatar_url = response["data"][0]["imageUrl"]

        if code not in description:
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Couldn't find the code in your profile. Please rerun the verify command in the server.", color=discord.Color.red()))
            return

        embed3 = discord.Embed(
            title=f"<:thunderbolt:987447657104560229> Thank you for verifying, {data['name']}!", color=discord.Color.nitro_pink())
        embed3.description = "You will now be able to attend to the shows hosted by **INKIGAYO**! If you want more benefits, you can purchase the VIP pass! Check <#1179028774545784943> for more information."
        embed3.set_thumbnail(url=avatar_url)

        data["avatar"] = avatar_url
        await add_roblox_info(interaction.user.id, data["id"], data)

        try:
            nickname = f"{data['displayName']} (@{data['name']})"
            if len(nickname) > 32:
                nickname = f"{data['name']}"

            await interaction.user.edit(nick=nickname)
        except:
            embed3.set_footer(
                text="I was not able to edit your nickname in the server")

        try:
            verified_role = interaction.guild.get_role(1183609826002079855)
            await interaction.user.add_roles(verified_role, reason=f"Verified account as: {nickname}")
        except:
            pass

        await interaction.user.send(embed=embed3)

    async def on_error(self, error: Exception, item, interaction: discord.Interaction) -> None:
        await interaction.user.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=discord.Color.red()))
        raise error


class DeleteRobloxAccountView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(disable_on_timeout=True)
        self.author = author

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(content="This button is not for you!", ephemeral=True)
        return False

    @discord.ui.button(label="Delete Account", emoji="<:delete:1055494235111034890>", style=discord.ButtonStyle.red)
    async def delete_callback(self, button, interaction: discord.Interaction):
        await delete_roblox_info(interaction.user.id)
        await interaction.response.edit_message(embed=discord.Embed(description="<:checked:1173356058387951626> Successfully deleted your Roblox info.", color=discord.Color.green()), view=None)


class VerifyViewPersistent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.Button(label="Verify", emoji="<:link:986648044525199390>", custom_id="verifypersistent")
    async def verify_persistent_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        roblox_data = await get_roblox_info(interaction.user.id)
        if roblox_data:
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            description = roblox_data["data"]["description"]

            embed = discord.Embed(
                title=f":wave: Hello there, {username}!", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)
            embed.add_field(name="Description", value=description)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            embed.description = "You are verified! If you wish to link another account, first delete your linked account using the button below and run this command again."
            return await interaction.followup.send(embed=embed, view=DeleteRobloxAccountView(interaction.user), ephemeral=True)

        await interaction.followup.send(content=":wave: To verify click the button below and follow the steps.", view=VerifyView(interaction.user), ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(VerifyViewPersistent())

    @commands.slash_command(description="Verify or delete your verified account with Sally")
    async def verify(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        roblox_data = await get_roblox_info(ctx.author.id)
        if roblox_data:
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            description = roblox_data["data"]["description"]

            embed = discord.Embed(
                title=f":wave: Hello there, {username}!", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)
            embed.add_field(name="Description", value=description)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            embed.description = "You are verified! If you wish to link another account, first delete your linked account using the button below and run this command again."
            return await ctx.respond(embed=embed, view=DeleteRobloxAccountView(ctx.author))

        await ctx.respond(content=":wave: To verify click the button below and follow the steps.", view=VerifyView(ctx.author))

    @commands.slash_command(description="Get someones Roblox information")
    async def getinfo(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to get the info from")):
        roblox_data = await get_roblox_info(user.id)
        if roblox_data:
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            description = roblox_data["data"]["description"]
            embed = discord.Embed(
                title=f"<:info:881973831974154250> Information for {username}", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            embed.description = description
            await ctx.respond(embed=embed)

        else:
            await ctx.respond(embed=discord.Embed(description="<:x_:1174507495914471464> This user is not linked with Sally.", color=discord.Color.red()))

    @commands.slash_command(description="Blacklist or unblacklist a user")
    async def blacklist(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to blacklist/unblacklist"), reason: discord.Option(str, "The reason of the blacklist", default="Blacklisted")):
        await ctx.defer()
        roblox_data = await get_roblox_info(user.id)
        if roblox_data:
            if not roblox_data["blacklisted"]:
                await blacklist_roblox_user(user.id, reason)
                await ctx.respond(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully **blacklisted** {user.mention} with Roblox account `{roblox_data['data']['name']}`. They will not be able to join INKIGAYO on Roblox.", color=discord.Color.green()))

            else:
                await remove_blacklist_roblox(user.id)
                await ctx.respond(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully **unblacklisted** {user.mention} with Roblox account `{roblox_data['data']['name']}`. They will be able to join INKIGAYO on Roblox.", color=discord.Color.green()))

        else:
            await ctx.respond(embed=discord.Embed(description="<:x_:1174507495914471464> This user is not linked with Sally."))

    @commands.command(name="forceverify")
    @commands.is_owner()
    async def force_verify(self, ctx: commands.Context, user_id: str, roblox_id: str):

        url = ROBLOX_USERS_ENDPOINT + roblox_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    await ctx.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID is invalid.", color=discord.Color.red()))
                    return
                data = await response.json()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={data['id']}&size=420x420&format=Png&isCircular=false") as resp:
                response = await resp.json()
                print(response)
                avatar_url = response["data"][0]["imageUrl"]

        data["avatar"] = avatar_url
        await add_roblox_info(user_id, roblox_id, data)
        member = ctx.guild.get_member(int(user_id))
        try:
            nickname = f"{data['displayName']} (@{data['name']})"
            if len(nickname) > 32:
                nickname = f"{data['name']}"

            await member.edit(nick=nickname)
        except:
            pass

        try:
            verified_role = ctx.guild.get_role(1183609826002079855)
            await member.add_roles(verified_role, reason=f"Verified account as: {nickname}")
        except:
            pass

        await ctx.send(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully forced verification on <@{user_id}> as Roblox account `{roblox_id}`", color=discord.Color.green()))

    @commands.command(name="verifymsg")
    async def verify_message(self, ctx: commands.Context, channel: discord.TextChannel):
        embed = discord.Embed(
            title="<:link:986648044525199390> Verfication Required!", color=discord.Color.nitro_pink())
        embed.description = "You are required to verify your Roblox account to be able to attend to our **INKIGAYO** shows. If you are not verified, you will not be able to join our Roblox game and be part of the audience.\n\n<:info:881973831974154250> All data stored is public information about your Roblox account. You can delete it at any time by clicking the button again or by using </verify:1183583727473917962> in a channel."

        embed.set_footer(text="If you run into any issues, please DM Dark")
        await channel.send(embed=embed, view=VerifyViewPersistent())
        await ctx.send(content="Sent!")


def setup(bot):
    bot.add_cog(Verification(bot))
