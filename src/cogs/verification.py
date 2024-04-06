import discord
from discord.ext import commands
from discord.interactions import Interaction
from resources.database import add_roblox_info, get_roblox_info, delete_roblox_info, blacklist_roblox_user, remove_blacklist_roblox, update_roblox_info, get_roblox_info_by_rbxid
from resources import webhook_manager
import asyncio
import aiohttp
import random
import datetime
import os
from resources import webhook_manager
from pymongo import results

words = ("INK", "GAYO", "ROBLOX", "SHOW", "POP",
         "MUSIC", "DRESS", "DANCE", "BEE", "CAT")

ROBLOX_USERS_ENDPOINT = "https://users.roblox.com/v1/users/"
ROBLOX_USERNAMES_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
api_key = os.getenv("ROBLOX_API_KEY")


class VerificationMethodsView(discord.ui.View):
    def __init__(self, roblox_id: int, avatar_url: str, username: str, guild: discord.Guild, roblox_data: dict, WEBHOOK_MESSAGE, LOG_EMBED):
        super().__init__(disable_on_timeout=True, timeout=60*5)
        self.roblox_id = roblox_id
        self.avatar_url = avatar_url
        self.username = username
        self.guild = guild
        self.roblox_data = roblox_data
        self.WEBHOOK_MESSAGE = WEBHOOK_MESSAGE
        self.LOG_EMBED = LOG_EMBED

    @discord.ui.button(label="Code Verification", style=discord.ButtonStyle.gray)
    async def code_verification(self, button, interaction: discord.Interaction):
        def code_check(message):
            return message.author.id == interaction.user.id and message.guild == None

        code = random.choice(words) + random.choice(words) + \
            random.choice(words) + random.choice(words)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Code Verification", color=discord.Color.nitro_pink())

        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{self.username}**,  please navigate to [your profile](https://roblox.com/users/{self.roblox_data['id']}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done, if you don't reply in 10 minutes, I will automatically check."
        embed2.add_field(
            name="<:editing:1174508480481218580> Code", value=str(code))

        embed2.set_thumbnail(url=self.avatar_url)

        embed2.set_author(
            name=f"Hello there, {self.username}!", icon_url=self.avatar_url)

        embed2.timestamp = datetime.datetime.now(datetime.UTC)
        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=self.guild.icon.url)

        await interaction.response.edit_message(embed=embed2, view=None)
        self.stop()

        try:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Waiting for Roblox code confirmation"], "pending", self.LOG_EMBED)
            await interaction.client.wait_for("message", check=code_check, timeout=60*10)
        except asyncio.TimeoutError:
            pass

        url = ROBLOX_USERS_ENDPOINT + str(self.roblox_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Invalid Roblox ID?"], "error", self.LOG_EMBED)
                    interaction.client.user_prompts.remove(interaction.user.id)
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()))
                    return
                new_roblox_data = await response.json()

        if code not in new_roblox_data["description"]:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["No code found in description"], "error", self.LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Couldn't find the code in your profile. Please rerun the verify command in the server.", color=discord.Color.red()))
            return

        self.roblox_data = new_roblox_data
        embed3 = discord.Embed(
            title=f"<:link:986648044525199390> Thank you for verifying, {self.roblox_data['name']}!", color=discord.Color.nitro_pink())
        embed3.description = "You will now be able to attend to the shows hosted by **INKIGAYO**!\n\n<:thunderbolt:987447657104560229> Want more benefits? You can purchase the VIP pass! Check <#1179028774545784943> for more information."
        embed3.set_thumbnail(url=self.avatar_url)

        errors = []

        self.roblox_data["avatar"] = self.avatar_url
        await add_roblox_info(interaction.user.id, self.roblox_data["id"], self.roblox_data)

        try:
            nickname = f"{self.roblox_data['displayName']} (@{self.roblox_data['name']})"
            if len(nickname) > 32:
                nickname = f"{self.roblox_data['name']}"

            elif self.roblox_data["displayName"] == self.roblox_data["name"]:
                nickname = self.roblox_data["name"]

            member = self.guild.get_member(interaction.user.id)
            await member.edit(nick=nickname)
        except:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Failed to edit nickname"], "pending", self.LOG_EMBED)
            errors.append("edit your nickname")

        try:
            verified_role = self.guild.get_role(1183609826002079855)
            member = self.guild.get_member(interaction.user.id)
            await member.add_roles(verified_role, reason=f"Verified account as: {nickname}")
        except:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Failed to add verified role"], "pending", self.LOG_EMBED)
            errors.append("assign your roles")

        if len(errors) > 0:
            errors_parsed = ", ".join(errors)
            embed3.set_footer(text="I was not able to: " +
                              errors_parsed + ". Please contact a staff member", icon_url=self.guild.icon.url)
        else:
            embed3.set_footer(text="INKIGAYO Verification",
                              icon_url=self.guild.icon.url)

        self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, [f"Completed verification. Account: {self.roblox_data['id']}"], "success", self.LOG_EMBED)
        interaction.client.user_prompts.remove(interaction.user.id)
        await interaction.user.send(embed=embed3)

    @discord.ui.button(label="Game Verification", style=discord.ButtonStyle.blurple)
    async def game_verification(self, button, interaction: discord.Interaction):

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Game Verification", color=discord.Color.nitro_pink())

        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{self.username}**,  please join the game I am providing you below. Follow the steps in-game and come back to this chat. If a join is not detected in 10 minutes, this prompt will be expire."

        embed2.timestamp = datetime.datetime.now(datetime.UTC)
        embed2.set_thumbnail(url=self.avatar_url)

        embed2.set_author(
            name=f"Hello there, {self.username}!", icon_url=self.avatar_url)

        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=self.guild.icon.url)

        button_view = discord.ui.View()
        button_view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Join Verification Game",
                             url="https://www.roblox.com/games/16462865396"))

        await interaction.response.edit_message(embed=embed2, view=button_view)
        self.stop()

        interaction.client.pending_verifications[str(self.roblox_id)] = {
            "username": str(interaction.user), "id": str(interaction.user.id)}

        def confirmation_check(roblox_id, discord_id):
            return int(roblox_id) == self.roblox_id and int(discord_id) == interaction.user.id

        try:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Waiting for Roblox game join"], "pending", self.LOG_EMBED)
            await interaction.client.wait_for("verification_completed", check=confirmation_check, timeout=60*10)
        except asyncio.TimeoutError:
            interaction.client.pending_verifications.pop(
                str(self.roblox_id))
            interaction.client.user_prompts.remove(interaction.user.id)
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["No game join detected"], "error", self.LOG_EMBED)
            return await interaction.user.send(content="<:x_:1174507495914471464> You took too long to join the game, please run `/verify` in the server again.")

        embed3 = discord.Embed(
            title=f"<:link:986648044525199390> Thank you for verifying, {self.roblox_data['name']}!", color=discord.Color.nitro_pink())
        embed3.description = "You will now be able to attend to the shows hosted by **INKIGAYO**!\n\n<:thunderbolt:987447657104560229> Want more benefits? You can purchase the VIP pass! Check <#1179028774545784943> for more information."
        embed3.set_thumbnail(url=self.avatar_url)

        errors = []

        self.roblox_data["avatar"] = self.avatar_url
        await add_roblox_info(interaction.user.id, self.roblox_data["id"], self.roblox_data)

        try:
            nickname = f"{self.roblox_data['displayName']} (@{self.roblox_data['name']})"
            if len(nickname) > 32:
                nickname = f"{self.roblox_data['name']}"

            elif self.roblox_data["displayName"] == self.roblox_data["name"]:
                nickname = self.roblox_data["name"]

            member = self.guild.get_member(interaction.user.id)
            await member.edit(nick=nickname)
        except:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Failed to edit nickname"], "warning", self.LOG_EMBED)
            errors.append("edit your nickname")

        try:
            verified_role = self.guild.get_role(1183609826002079855)
            member = self.guild.get_member(interaction.user.id)
            await member.add_roles(verified_role, reason=f"Verified account as: {nickname}")
        except:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["Failed to add verified role"], "warning", self.LOG_EMBED)
            errors.append("assign your roles")

        if len(errors) > 0:
            errors_parsed = ", ".join(errors)
            embed3.set_footer(text="I was not able to: " +
                              errors_parsed + ". Please contact a staff member", icon_url=self.guild.icon.url)
        else:
            embed3.set_footer(text="INKIGAYO Verification",
                              icon_url=self.guild.icon.url)

        interaction.client.user_prompts.remove(interaction.user.id)

        self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, [f"Completed verification. Account: {self.roblox_data['id']}"], "success", self.LOG_EMBED)
        await interaction.user.send(embed=embed3)


class VerifyView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(disable_on_timeout=True)
        self.author = author

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(content="This button is not for you!", ephemeral=True)
        return False

    async def validate_username(self, username: str):
        data = {"usernames": [username], "excludeBannedUsers": True}
        headers = {"accept": "application/json",
                   "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(ROBLOX_USERNAMES_ENDPOINT, json=data, headers=headers) as resp:
                response = await resp.json()
                if len(response["data"]) == 0:
                    return False, None, None

                return True, response["data"][0]["id"], response["data"][0]["name"]

    @discord.ui.button(emoji="<:link:986648044525199390>", label="Verify Roblox account")
    async def verify_button(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        if interaction.user.id in interaction.client.user_prompts:
            return await interaction.followup.send(embed=discord.Embed(description="<:x_:1174507495914471464> You are already in a verification process. Please finish it before starting another one.", color=discord.Color.red()), ephemeral=True)

        interaction.client.user_prompts.append(interaction.user.id)

        WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.send_log(interaction.user, ["Started verification process"], "pending")
        print(WEBHOOK_MESSAGE)
        if WEBHOOK_MESSAGE is None or LOG_EMBED is None:
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.followup.send(embed=discord.Embed(description="<:x_:1174507495914471464> Something went wrong, please try again.", color=discord.Color.red()), ephemeral=True)

        try:
            embed1 = discord.Embed(
                title=f"<:link:986648044525199390> Roblox Information", color=discord.Color.nitro_pink())
            embed1.description = "Welcome to the verification process to link your Roblox account with Sally! This will only take five minutes.\nPlease provide me your **Roblox username**, not your display name.\n\n<:info:881973831974154250> All data stored is public information about your Roblox account. You can delete it at any time by using </verify:1183583727473917962> in a channel."
            embed1.timestamp = datetime.datetime.now(datetime.UTC)
            embed1.set_author(
                name=f"Hello there, {interaction.user.display_name}!", icon_url=interaction.user.display_avatar.url)
            embed1.set_footer(text="This prompt will expire in 10 minutes",
                              icon_url=interaction.guild.icon.url)

            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Sent initial DM"], "pending", LOG_EMBED)
            msg = await interaction.user.send(embed=embed1)
            await interaction.followup.send(embed=discord.Embed(description=f"<:sally:1225256761154600971> I have sent you a direct message! Please head to our chat: https://discord.com/channels/@me/{msg.channel.id}/{msg.id}", color=discord.Color.nitro_pink()), ephemeral=True)
        except:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Failed to send a DM"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.followup.send(embed=discord.Embed(description="<:x_:1174507495914471464> Please open your DMs and try again!", color=discord.Color.red()), ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == interaction.user.id and message.guild == None

        try:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Asking Roblox username"], "pending", LOG_EMBED)
            roblox_username = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Roblox username prompt timed out"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> Your prompt timed out.", color=discord.Color.red()))

        roblox_username = roblox_username.content

        validation, roblox_id, roblox_username = await self.validate_username(roblox_username)
        if not validation:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Invalid Roblox username"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox username you provided does not exist. Please rerun the verify command in the server.", color=discord.Color.red()))

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={roblox_id}&size=420x420&format=Png&isCircular=false") as resp:
                response = await resp.json()
                avatar_url = response["data"][0]["imageUrl"]

        url = ROBLOX_USERS_ENDPOINT + str(roblox_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Invalid Roblox ID?"], "error", LOG_EMBED)
                    interaction.client.user_prompts.remove(interaction.user.id)
                    await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> The Roblox ID you originally provided me was wrong or invalid. Please try again and check the data you are providing.", color=discord.Color.red()))
                    return
                roblox_data = await response.json()

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=discord.Color.nitro_pink())
        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{roblox_username}**, Please select one of the verification methods I am providing you below.\n\n<:rightarrow:1173350998388002888> **Code Verification**: I will provide you a code to paste in your Roblox profile.\n<:rightarrow:1173350998388002888> **Game Verification**: I will provide you a game to join and complete the verification process."
        embed2.timestamp = datetime.datetime.now(datetime.UTC)
        embed2.set_thumbnail(url=avatar_url)
        embed2.set_author(
            name=f"Hello there, {roblox_username}!", icon_url=avatar_url)
        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=interaction.guild.icon.url)

        verifyMethodView = VerificationMethodsView(
            roblox_id, avatar_url, roblox_username, interaction.guild, roblox_data, WEBHOOK_MESSAGE, LOG_EMBED)
        await interaction.user.send(embed=embed2, view=verifyMethodView)
        WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Waiting for method selection"], "pending", LOG_EMBED)
        if await verifyMethodView.wait():
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Method selection timed out"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            await interaction.user.send(embed=discord.Embed(description="<:x_:1174507495914471464> You took too long to select a verification method, please run `/verify` in the server again.", color=discord.Color.red()))

    async def on_error(self, error: Exception, item, interaction: discord.Interaction) -> None:
        await interaction.user.send(embed=discord.Embed(description=f"<:x_:1174507495914471464> Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=discord.Color.red()))
        interaction.client.user_prompts.remove(interaction.user.id)
        await webhook_manager.send(
            f"❗️ Failed to complete verification process for {interaction.user} ({interaction.user.id}) because of: {error}. Traceback:")
        await webhook_manager.send_verification_error(interaction, error)
        raise error


class ManageRobloxAccountView(discord.ui.View):
    def __init__(self, author: discord.Member, user_id: str, roblox_id: str, managed: bool = False):
        super().__init__(disable_on_timeout=True)
        self.author = author
        self.user_id = user_id
        self.roblox_id = roblox_id
        self.managed = managed

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(content="This button is not for you!", ephemeral=True)
        return False

    @discord.ui.button(label="Delete Account", emoji="<:delete:1055494235111034890>", style=discord.ButtonStyle.red)
    async def delete_callback(self, button, interaction: discord.Interaction):
        roblox_data = await get_roblox_info(str(self.user_id))
        if not self.managed:
            if roblox_data["blacklisted"]:
                return await interaction.response.send_message(embed=discord.Embed(description="<:x_:1174507495914471464> You can't delete your Roblox data while being blacklisted. Please contact Dark if you wish to delete your data.", color=discord.Color.red()), ephemeral=True)

        await delete_roblox_info(str(self.user_id))
        member = interaction.guild.get_member(int(roblox_data["user_id"]))
        await webhook_manager.send_log(member, ["Deleted Roblox data"], "warning")
        try:
            await member.edit(nick=None)
        except:
            pass

        try:
            verified_role = interaction.guild.get_role(1183609826002079855)
            await member.remove_roles(verified_role)
        except:
            pass
        await interaction.response.edit_message(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully deleted {'the' if self.managed else 'your'} Roblox data.", color=discord.Color.green()), view=None)
        self.stop()

    @discord.ui.button(label="Refresh Data", emoji="<:reload:1179444707114352723>")
    async def refresh_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        url = ROBLOX_USERS_ENDPOINT + str(self.roblox_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={data['id']}&size=420x420&format=Png&isCircular=false") as resp:
                response = await resp.json()
                avatar_url = response["data"][0]["imageUrl"]

        data["avatar"] = avatar_url
        roblox_data = await update_roblox_info(self.user_id, self.roblox_id, data)
        member = interaction.guild.get_member(int(roblox_data["user_id"]))
        await webhook_manager.send_log(member, ["Refreshed Roblox data"], "warning")
        try:
            nickname = f"{data['displayName']} (@{data['name']})"
            if len(nickname) > 32:
                nickname = f"{data['name']}"

            await member.edit(nick=nickname)
        except:
            pass

        username = roblox_data["data"]["name"]
        avatar_url = roblox_data["data"]["avatar"]
        display_name = roblox_data["data"]["displayName"]
        roblox_id = roblox_data["data"]["id"]
        created = roblox_data["data"]["created"]
        created = discord.utils.format_dt(
            datetime.datetime.fromisoformat(created), "R")

        embed = discord.Embed(
            title=f":wave: Hello there, {username}!", color=discord.Color.nitro_pink())
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="Display Name", value=display_name)
        embed.add_field(name="Roblox ID", value=roblox_id)
        embed.add_field(name="Created", value=created)

        if roblox_data["blacklisted"]:
            embed.add_field(name="Blacklist Info",
                            value=str(roblox_data["message"]))

        if self.managed:
            embed.description = "Description:\n" + \
                roblox_data["data"]["description"]
            embed.title = f"<:info:881973831974154250> Roblox Information for {username}"
        else:
            embed.description = "You are verified! You are able to attend to our **INKIGAYOS** in Roblox.\n\n<:info:881973831974154250> If you wish to **link another account**, first delete your linked account using the `Delete Account` button below and run this command again.\nIf your **Roblox information** is **outdated**, click the `Refresh Data` button."
        await interaction.edit_original_response(embed=embed)
        await interaction.followup.send(embed=discord.Embed(description="<:checked:1173356058387951626> Successfully refreshed the Roblox data.", color=discord.Color.green()), ephemeral=True)


class VerifyViewPersistent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", emoji="<:link:986648044525199390>", custom_id="verifypersistent")
    async def verify_persistent_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        roblox_data = await get_roblox_info(interaction.user.id)
        if roblox_data:
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            created = roblox_data["data"]["created"]
            created = discord.utils.format_dt(
                datetime.datetime.fromisoformat(created), "R")

            embed = discord.Embed(
                title=f":wave: Hello there, {username}!", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)
            embed.add_field(name="Created", value=created)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            nickname = f"{display_name} (@{username})"
            if len(nickname) > 32:
                nickname = username
            elif display_name == username:
                nickname = username

            if interaction.user.display_name != nickname:
                try:
                    await interaction.user.edit(nick=nickname)
                except:
                    pass

            embed.description = "You are verified! You are able to attend to our **INKIGAYOS** in Roblox.\n\n<:info:881973831974154250> If you wish to **link another account**, first delete your linked account using the `Delete Account` button below and run this command again.\nIf your **Roblox information** is **outdated**, click the `Refresh Data` button."
            return await interaction.followup.send(embed=embed, view=ManageRobloxAccountView(interaction.user, interaction.user.id, roblox_id), ephemeral=True)

        await interaction.followup.send(content=":wave: To verify click the button below and follow the steps.", view=VerifyView(interaction.user), ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(VerifyViewPersistent())

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == 1170821546038800464:
            result: results.DeleteResult = await delete_roblox_info(member.id)
            if result.deleted_count != 0:
                await webhook_manager.send_log(member, ["User left the guild", "Deleted Roblox data"], "warning")

    @commands.slash_command(description="Verify or delete your verified account with Sally")
    @commands.guild_only()
    async def verify(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        roblox_data = await get_roblox_info(ctx.author.id)

        if roblox_data:
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            created = roblox_data["data"]["created"]
            created = discord.utils.format_dt(
                datetime.datetime.fromisoformat(created), "R")

            embed = discord.Embed(
                title=f":wave: Hello there, {username}!", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)
            embed.add_field(name="Created", value=created)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            nickname = f"{display_name} (@{username})"
            if len(nickname) > 32:
                nickname = username
            elif display_name == username:
                nickname = username

            if ctx.author.display_name != nickname:
                try:
                    await ctx.author.edit(nick=nickname)
                except:
                    pass

            embed.description = "You are verified! You are able to attend to our **INKIGAYOS** in Roblox.\n\n<:info:881973831974154250> If you wish to **link another account**, first delete your linked account using the `Delete Account` button below and run this command again.\nIf your **Roblox information** is **outdated**, click the `Refresh Data` button."
            return await ctx.respond(embed=embed, view=ManageRobloxAccountView(ctx.author, ctx.author.id, roblox_id))

        await ctx.respond(content=":wave: To verify click the button below and follow the steps.", view=VerifyView(ctx.author))

    @commands.slash_command(description="Get someones Roblox information")
    @commands.guild_only()
    async def getinfo(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to get the info from", default=None), roblox_id: discord.Option(str, "The Roblox ID to look up for", default=None)):  # type: ignore
        if user and roblox_id:
            return await ctx.respond(embed=discord.Embed(description="<:x_:1174507495914471464> You have to either provide a `user` **or** `roblox_id`.", color=discord.Color.red()))
        elif not user and not roblox_id:
            user = ctx.author

        await ctx.defer()

        if user:
            roblox_data = await get_roblox_info(user.id)
        elif roblox_id:
            roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        else:
            return await ctx.respond(embed=await ctx.respond(embed=discord.Embed(description="<:x_:1174507495914471464> Something went wrong while choosing how to fetch the data. Try again.", color=discord.Color.red())))

        if roblox_data:
            fetched_member = ctx.guild.get_member(
                int(roblox_data["user_id"])) if not user else user
            username = roblox_data["data"]["name"]
            avatar_url = roblox_data["data"]["avatar"]
            display_name = roblox_data["data"]["displayName"]
            roblox_id = roblox_data["data"]["id"]
            description = roblox_data["data"]["description"]
            created = roblox_data["data"]["created"]
            created = discord.utils.format_dt(
                datetime.datetime.fromisoformat(created), "R")
            embed = discord.Embed(
                title=f"<:info:881973831974154250> Roblox Information for {username}", color=discord.Color.nitro_pink())
            embed.set_thumbnail(url=avatar_url)

            if fetched_member:
                embed.add_field(
                    name="Discord Account", value=f"{fetched_member.mention} (`{fetched_member.id}`)")
            else:
                embed.add_field(name="Discord Account",
                                value=f"Could not fetch information")

            embed.add_field(name="Roblox Display Name", value=display_name)
            embed.add_field(name="Roblox ID", value=roblox_id)
            embed.add_field(name="Created", value=created)

            if roblox_data["blacklisted"]:
                embed.add_field(name="Blacklist Info",
                                value=str(roblox_data["message"]))

            embed.description = "Description:\n" + description
            if self.bot.is_owner(ctx.author):
                view = ManageRobloxAccountView(
                    ctx.author, roblox_data["user_id"], roblox_id, managed=True)
            else:
                view = None

            await ctx.respond(embed=embed, view=view)

        else:
            await ctx.respond(embed=discord.Embed(description="<:x_:1174507495914471464> This user is not linked with Sally.", color=discord.Color.red()))

    @commands.slash_command(description="Blacklist or unblacklist a user")
    async def blacklist(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to blacklist/unblacklist"), reason: discord.Option(str, "The reason of the blacklist", default="Blacklisted")):  # type: ignore
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
                avatar_url = response["data"][0]["imageUrl"]

        data["avatar"] = avatar_url
        await add_roblox_info(user_id, roblox_id, data)
        member = ctx.guild.get_member(int(user_id))
        try:
            nickname = f"{data['displayName']} (@{data['name']})"
            if len(nickname) > 32:
                nickname = f"{data['name']}"
            elif data["displayName"] == data["name"]:
                nickname = data["name"]

            await member.edit(nick=nickname)
        except:
            pass

        try:
            verified_role = ctx.guild.get_role(1183609826002079855)
            await member.add_roles(verified_role, reason=f"Verified account as: {nickname}")
        except:
            pass

        await ctx.reply(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully forced verification on {member.mention} as Roblox account `{roblox_id}`", color=discord.Color.green()), mention_author=False)

    @commands.command(name="forceunverify")
    @commands.is_owner()
    async def force_unverify(self, ctx: commands.Context, user_id: str):
        member = ctx.guild.get_member(int(user_id))

        await delete_roblox_info(user_id)

        try:
            await member.edit(nick=None)
        except:
            pass

        try:
            role = ctx.guild.get_role(1183609826002079855)
            await member.remove_roles(role)
        except:
            pass

        await ctx.reply(embed=discord.Embed(description=f"<:checked:1173356058387951626> Successfully forced unverification on {member.mention}.", color=discord.Color.green()), mention_author=False)

    @commands.command(name="verifymsg")
    @commands.is_owner()
    async def verify_message(self, ctx: commands.Context, channel: discord.TextChannel):
        embed = discord.Embed(
            title="<:link:986648044525199390> Verfication Required!", color=discord.Color.nitro_pink())
        embed.description = "You are required to verify your Roblox account to be able to attend to our **INKIGAYO** shows. If you are not verified, you will not be able to join our Roblox game and be part of the audience.\n\n<:info:881973831974154250> All data stored is public information about your Roblox account. You can delete it at any time by clicking the button again or by using </verify:1183583727473917962> in a channel. Data gets automatically deleted if you leave this server.\n\n<:lifesaver:986648046592983150> Having issues? Please DM <@449245847767482379> with relevant information about your issue."

        embed.set_footer(
            text="INKIGAYO Roblox - Verification")
        await channel.send(embed=embed, view=VerifyViewPersistent())
        await ctx.send(content="Sent!")


def setup(bot):
    bot.add_cog(Verification(bot))
