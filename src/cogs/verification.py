import aiohttp
import asyncio
import datetime
import discord
from discord.ext import commands
from discord.interactions import Interaction
import os
from pymongo import results
from resources import database as db
from resources import webhook_manager, verification, aesthetic
import random


words = ("ARTISTS", "SONGS", "ROBLOX", "SHOW", "POP",
         "MUSIC", "LIGHTS", "DANCE", "BEE", "CAT", "WEPEAK")


class VerificationMethodsView(discord.ui.View):
    def __init__(self, roblox_id: int, username: str, guild: discord.Guild, roblox_data: dict, WEBHOOK_MESSAGE, LOG_EMBED):
        super().__init__(disable_on_timeout=True, timeout=60*5)
        self.roblox_id = roblox_id
        self.avatar_url = roblox_data["avatar_url"]
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
            title=f"{aesthetic.Emojis.user} Code Verification", color=aesthetic.Colors.main)

        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{self.username}**,  please navigate to [your profile](https://roblox.com/users/{self.roblox_data['id']}/profile) and paste the code I am providing you below in your **about me**.\n\nSay `done` or send any message here when you are done, if you don't reply in 10 minutes, I will automatically check."
        embed2.add_field(
            name=f"{aesthetic.Emojis.edit} Code", value=str(code))

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

        description = await verification.fetch_roblox_description(self.roblox_id)

        if code not in description:
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, ["No code found in description"], "error", self.LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Couldn't find the code in your profile. Please rerun the verify command in the server.", color=aesthetic.Colors.error))
            return

        embed3 = discord.Embed(
            title=f"{aesthetic.Emojis.link} Thank you for verifying, {self.roblox_data['name']}!", color=aesthetic.Colors.main)
        embed3.description = f"You will now be able to attend events hosted by **WePeak**!\n\n{aesthetic.Emojis.thunderbolt} **Want more benefits?** You can purchase the **WePeak Pass** and claim the role on your profile settings when using `/verify`"
        embed3.set_thumbnail(url=self.avatar_url)

        errors = await verification.update_discord_profile(self.guild, interaction.user.id, self.roblox_data)
        if len(errors) > 0:
            errors_parsed = ", ".join(errors)
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, errors, "pending", self.LOG_EMBED)
            embed3.set_footer(text="I was not able to: " +
                              errors_parsed + ". Please contact a staff member", icon_url=self.guild.icon.url)

        await db.add_roblox_info(interaction.user.id, self.roblox_data["id"], self.roblox_data)

        '''
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
        '''

        self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, [f"Completed verification. Account: {self.roblox_data['id']}"], "success", self.LOG_EMBED)
        interaction.client.user_prompts.remove(interaction.user.id)
        await interaction.user.send(embed=embed3)

    @discord.ui.button(label="Game Verification", style=discord.ButtonStyle.blurple)
    async def game_verification(self, button, interaction: discord.Interaction):

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Game Verification", color=aesthetic.Colors.main)

        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{self.username}**,  please join the game I am providing you below. Follow the steps in-game and come back to this chat. If a join is not detected in 10 minutes, this prompt will be expire."

        embed2.timestamp = datetime.datetime.now(datetime.UTC)
        embed2.set_thumbnail(url=self.avatar_url)

        embed2.set_author(
            name=f"Hello there, {self.username}!", icon_url=self.avatar_url)

        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=self.guild.icon.url)

        button_view = discord.ui.View()
        button_view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Join Verification Game",
                             url="https://www.roblox.com/games/16441883725/Sally-Verification-Game"))

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
            return await interaction.user.send(content=f"{aesthetic.Colors.secondary} You took too long to join the game, please run `/verify` in the server again.")

        embed3 = discord.Embed(
            title=f"{aesthetic.Emojis.link} Thank you for verifying, {self.roblox_data['name']}!", color=aesthetic.Colors.main)
        embed3.description = f"You will now be able to attend events hosted by **WePeak**!\n\n{aesthetic.Emojis.thunderbolt} **Want more benefits?** You can purchase the **WePeak Pass** and claim the role on your profile settings when using `/verify`"
        embed3.set_thumbnail(url=self.avatar_url)

        errors = await verification.update_discord_profile(self.guild, interaction.user.id, self.roblox_data)
        if len(errors) > 0:
            errors_parsed = ", ".join(errors)
            self.WEBHOOK_MESSAGE, self.LOG_EMBED = await webhook_manager.update_log(self.WEBHOOK_MESSAGE, errors, "pending", self.LOG_EMBED)
            embed3.set_footer(text="I was not able to: " +
                              errors_parsed + ". Please contact a staff member", icon_url=self.guild.icon.url)

        await db.add_roblox_info(interaction.user.id, self.roblox_data["id"], self.roblox_data)
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
            async with session.post("https://users.roblox.com/v1/usernames/users", json=data, headers=headers) as resp:
                response = await resp.json()
                if len(response["data"]) == 0:
                    return False, None, None

                return True, response["data"][0]["id"], response["data"][0]["name"]

    @discord.ui.button(emoji=aesthetic.Emojis.link, label="Verify Roblox account")
    async def verify_button(self, button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        if interaction.user.id in interaction.client.user_prompts:
            return await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You are already in a verification process. Please check your DMs for the active prompt.", color=aesthetic.Colors.error), ephemeral=True)

        interaction.client.user_prompts.append(interaction.user.id)

        WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.send_log(interaction.user, ["Started verification process"], "pending")
        print(WEBHOOK_MESSAGE)
        if WEBHOOK_MESSAGE is None or LOG_EMBED is None:
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Something went wrong, please try again.", color=aesthetic.Colors.error), ephemeral=True)

        try:
            embed1 = discord.Embed(
                title=f"{aesthetic.Emojis.link} Roblox Information", color=aesthetic.Colors.main)
            embed1.description = "Welcome to the verification process to link your Roblox account with Sally! This will only take five minutes.\nPlease provide me your **Roblox username**, not your display name.\n\n<:info:881973831974154250> All data stored is public information about your Roblox account. You can delete it at any time by using </verify:1183583727473917962> in a channel."
            embed1.timestamp = datetime.datetime.now(datetime.UTC)
            embed1.set_author(
                name=f"Hello there, {interaction.user.display_name}!", icon_url=interaction.user.display_avatar.url)
            embed1.set_footer(text="This prompt will expire in 10 minutes",
                              icon_url=interaction.guild.icon.url)

            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Sent initial DM"], "pending", LOG_EMBED)
            msg = await interaction.user.send(embed=embed1)
            await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.sally} I have sent you a direct message! Please head to our chat: https://discord.com/channels/@me/{msg.channel.id}/{msg.id}", color=aesthetic.Colors.main), ephemeral=True)
        except:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Failed to send a DM"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Please open your DMs and try again!", color=aesthetic.Colors.error), ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == interaction.user.id and message.guild == None

        try:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Asking Roblox username"], "pending", LOG_EMBED)
            roblox_username = await interaction.client.wait_for("message", check=check, timeout=60*10)
        except asyncio.TimeoutError:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Roblox username prompt timed out"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You took too long to provide me your Roblox username. Please run `/verify` in the server again.", color=aesthetic.Colors.error))

        roblox_username = roblox_username.content

        # Validate an account with that username exists
        validation, roblox_id, roblox_username = await self.validate_username(roblox_username)
        if not validation:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Invalid Roblox username"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} The Roblox username you provided does not exist. Please rerun the verify command in the server.", color=aesthetic.Colors.error))

        # Validate if the Roblox account is already linked
        temp_roblox_data = await db.get_roblox_info_by_rbxid(roblox_id)
        if temp_roblox_data:
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Roblox ID already linked"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            return await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} This Roblox account is already linked with another Discord account. You must unlink your Roblox account from the other Discord account if you wish to verify as this account.", color=aesthetic.Colors.error))

        roblox_data = await verification.fetch_roblox_data(roblox_id)

        embed2 = discord.Embed(
            title="<:user:988229844301131776> Identity confirmation", color=aesthetic.Colors.main)
        embed2.description = f"Thank you, {interaction.user.display_name}! We will need to confirm you indeed own **{roblox_username}**, Please select one of the verification methods I am providing you below.\n\n<:rightarrow:1173350998388002888> **Code Verification**: I will provide you a code to paste in your Roblox profile.\n<:rightarrow:1173350998388002888> **Game Verification**: I will provide you a game to join and complete the verification process."
        embed2.timestamp = datetime.datetime.now(datetime.UTC)
        embed2.set_thumbnail(url=roblox_data["avatar_url"])
        embed2.set_author(
            name=f"Hello there, {roblox_username}!", icon_url=roblox_data["avatar_url"])
        embed2.set_footer(text="This prompt will expire in 10 minutes",
                          icon_url=interaction.guild.icon.url)

        # Continue with verification method selection
        verifyMethodView = VerificationMethodsView(
            roblox_id, roblox_username, interaction.guild, roblox_data, WEBHOOK_MESSAGE, LOG_EMBED)
        await interaction.user.send(embed=embed2, view=verifyMethodView)
        WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Waiting for method selection"], "pending", LOG_EMBED)

        # Verification method view timed out
        if await verifyMethodView.wait():
            WEBHOOK_MESSAGE, LOG_EMBED = await webhook_manager.update_log(WEBHOOK_MESSAGE, ["Method selection timed out"], "error", LOG_EMBED)
            interaction.client.user_prompts.remove(interaction.user.id)
            await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You took too long to select a verification method. Please run `/verify` in the server again.", color=aesthetic.Colors.error))

    async def on_error(self, error: Exception, item, interaction: discord.Interaction) -> None:
        await interaction.user.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Something went wrong, please contact Dark and send him the text below:\n\n```\n{error}```", color=aesthetic.Colors.error))
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

        if verification.VIP_ROLE_ID in [role.id for role in author.roles] or self.managed:
            self.children[2].disabled = True

        if self.managed:
            self.add_item(discord.ui.Button(
                label="You are able to manage this account", emoji=aesthetic.Emojis.info, disabled=True, row=1))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(content="This button is not for you!", ephemeral=True)
        return False

    @discord.ui.button(label="Delete Account", emoji="<:delete:1055494235111034890>", style=discord.ButtonStyle.red)
    async def delete_callback(self, button, interaction: discord.Interaction):
        roblox_data = await db.get_roblox_info(str(self.user_id))
        if not self.managed:
            if roblox_data["blacklisted"]:
                return await interaction.response.send_message(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You can't delete your Roblox data while being blacklisted. Please contact Dark if you wish to delete your data.", color=aesthetic.Colors.error), ephemeral=True)

        await db.delete_roblox_info(str(self.user_id))
        member = interaction.guild.get_member(int(roblox_data["user_id"]))
        await webhook_manager.send_log(member, ["Deleted Roblox data"], "warning")
        try:
            await member.edit(nick=None)
        except:
            pass

        try:
            await member.remove_roles(discord.Object(id=verification.VERIFIED_ROLE_ID), reason="Deleted Roblox data")
        except:
            pass
        await interaction.response.edit_message(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully deleted {'the' if self.managed else 'your'} Roblox data.", color=aesthetic.Colors.success), view=None)
        self.stop()

    @discord.ui.button(label="Refresh Data", emoji="<:reload:1179444707114352723>")
    async def refresh_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data = await verification.fetch_roblox_data(self.roblox_id)
        roblox_data = await db.update_roblox_info(self.user_id, self.roblox_id, data)
        member = interaction.guild.get_member(int(roblox_data["user_id"]))
        await webhook_manager.send_log(member, ["Refreshed Roblox data"], "warning")
        try:
            nickname = f"{data['displayName']} (@{data['name']})"
            if len(nickname) > 32:
                nickname = f"{data['name']}"

            await member.edit(nick=nickname)
        except:
            pass

        embed = await verification.Embeds.profile_embed(data, self.managed)
        await interaction.edit_original_response(embed=embed)
        await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully refreshed the Roblox data.", color=aesthetic.Colors.success), ephemeral=True)

    @discord.ui.button(label="WePeak Pass", emoji=aesthetic.Emojis.thunderbolt, style=discord.ButtonStyle.blurple)
    async def wepeak_pass_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        roblox_data = await db.get_roblox_info(interaction.user.id)
        if not roblox_data:
            return await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You are not verified with Sally! Use `/verify` in a channel to verify.", color=aesthetic.Colors.error), ephemeral=True)

        user_id = roblox_data["roblox_id"]
        # 17538362448
        g_url = f"https://inventory.roblox.com/v1/users/{user_id}/items/1/815912807/is-owned"
        async with aiohttp.ClientSession() as session:
            async with session.get(g_url) as response:
                resp = await response.json()
                if not resp:
                    link_button = discord.ui.Button(
                        style=discord.ButtonStyle.link, label="Buy WePeak Pass", url="https://www.roblox.com/game-pass/815912807")
                    view = discord.ui.View(link_button)
                    await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.sally} Please buy the gamepass before claiming the Discord role!", color=aesthetic.Colors.secondary), view=view, ephemeral=True)
                    return
        try:
            await interaction.user.add_roles(discord.Object(id=verification.VIP_ROLE_ID), reason=f"Bought VIP for Roblox account: {user_id}")
        except:
            return await interaction.followup.send(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Something went wrong while assigning the role. Please contact a staff member.", color=aesthetic.Colors.error), ephemeral=True)

        embed3 = discord.Embed(
            title=f"{aesthetic.Emojis.thunderbolt} Thank you for purchasing the **WePeak Pass**, {interaction.user.display_name}!", color=aesthetic.Colors.main)
        embed3.description = f"I have assigned your roles and you are now part of the **WePeak Pass Members**! Enjoy these benefits for **all** of the events hosted by **WePeak** and thank you for supporting us!\n{aesthetic.Emojis.sally} If you do not see the VIP role in your server profile, please contact a staff member."
        await interaction.followup.send(embed=embed3, ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == 1240592168754745414:
            result: results.DeleteResult = await db.delete_roblox_info(member.id)
            if result.deleted_count != 0:
                await webhook_manager.send_log(member, ["User left the guild", "Deleted Roblox data"], "warning")

    @commands.slash_command(description="Verify or delete your verified account with Sally")
    @commands.guild_only()
    async def verify(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        roblox_data = await db.get_roblox_info(ctx.author.id)

        if roblox_data:
            updated = await verification.attempt_avatar_refresh(roblox_data)
            if updated:
                roblox_data = await db.update_roblox_info(ctx.author.id, roblox_data["roblox_id"], updated)
                await verification.update_discord_profile(ctx.guild, ctx.author.id, roblox_data["data"])

            embed = await verification.Embeds.profile_embed(roblox_data)
            return await ctx.respond(embed=embed, view=ManageRobloxAccountView(ctx.author, ctx.author.id, roblox_data["roblox_id"]))

        await ctx.respond(content=":wave: To verify click the button below and follow the steps.", view=VerifyView(ctx.author))

    @commands.slash_command(description="Get someones Roblox information")
    @commands.guild_only()
    async def getinfo(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to get the info from", default=None), roblox_id: discord.Option(str, "The Roblox ID to look up for", default=None)):  # type: ignore
        if user and roblox_id:
            return await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.error} You have to either provide a `user` **or** `roblox_id`.", color=aesthetic.Colors.error))
        elif not user and not roblox_id:
            user = ctx.author

        await ctx.defer()

        if user:
            roblox_data = await db.get_roblox_info(user.id)
        elif roblox_id:
            roblox_data = await db.get_roblox_info_by_rbxid(roblox_id)
        else:
            return await ctx.respond(embed=await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Something went wrong while choosing how to fetch the data. Try again.", color=aesthetic.Colors.error)))

        managed = await self.bot.is_owner(ctx.author)
        if roblox_data:
            embed = await verification.Embeds.profile_embed(roblox_data, managed)

            if managed:
                view = ManageRobloxAccountView(
                    ctx.author, roblox_data["user_id"], roblox_id, managed)
            else:
                view = None

            await ctx.respond(embed=embed, view=view)

        else:
            await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.error} This user is not linked with Sally.", color=aesthetic.Colors.error))

    @commands.slash_command(description="Blacklist or unblacklist a user")
    @commands.is_owner()
    async def blacklist(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to blacklist/unblacklist"), reason: discord.Option(str, "The reason of the blacklist", default="Blacklisted")):  # type: ignore
        await ctx.defer()
        roblox_data = await db.get_roblox_info(user.id)
        if roblox_data:
            if not roblox_data["blacklisted"]:
                await db.blacklist_roblox_user(user.id, reason)
                await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully **blacklisted** {user.mention} with Roblox account `{roblox_data['data']['name']}`.", color=aesthetic.Colors.success))

            else:
                await db.remove_blacklist_roblox(user.id)
                await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully **unblacklisted** {user.mention} with Roblox account `{roblox_data['data']['name']}`.", color=aesthetic.Colors.success))

        else:
            await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.error} This user is not linked with Sally."))

    @commands.command(name="checkalts")
    @commands.is_owner()
    async def check_alts(self, ctx: commands.Context, roblox_id: str):
        roblox_data_list = await db.find("roblox_verifications", {"roblox_id": roblox_id})
        if len(roblox_data_list) > 1:
            discord_ids = [roblox_data["user_id"]
                           for roblox_data in roblox_data_list]
            return await ctx.reply(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Found more than one account linked to {roblox_id}: `{', '.join(discord_ids)}`", color=aesthetic.Colors.main), mention_author=False)
        return await ctx.reply(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Did not find more than one account linked to {roblox_id}.", color=aesthetic.Colors.success), mention_author=False)

    @commands.command(name="checklock")
    @commands.is_owner()
    async def check_lock(self, ctx: commands.Context, roblox_id: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://sally.darks.tech/lock/check-user?roblox_id={roblox_id}", headers={"Authorization": os.getenv("API_AUTHORIZATION_CODE")}) as resp:
                response = await resp.text()

        await ctx.reply(embed=discord.Embed(description=f"```json\n{response}\n```", color=aesthetic.Colors.main), mention_author=False)

    @commands.command(name="forceverify")
    @commands.is_owner()
    async def force_verify(self, ctx: commands.Context, user_id: str, roblox_id: str):

        roblox_data = await verification.fetch_roblox_data(roblox_id)
        await db.add_roblox_info(user_id, roblox_id, roblox_data)

        await ctx.reply(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully forced verification on <@{user_id}> as Roblox account `{roblox_id}`", color=aesthetic.Colors.success), mention_author=False)

    @commands.command(name="forceunverify")
    @commands.is_owner()
    async def force_unverify(self, ctx: commands.Context, user_id: str):
        member = ctx.guild.get_member(int(user_id))

        await db.delete_roblox_info(user_id)

        try:
            await member.edit(nick=None)
        except:
            pass

        try:
            await member.remove_roles(discord.Object(id=verification.VERIFIED_ROLE_ID), reason="Forced unverification")
        except:
            pass

        await ctx.reply(embed=discord.Embed(description=f"{aesthetic.Emojis.success} Successfully forced unverification on {member.mention}.", color=aesthetic.Colors.success), mention_author=False)


def setup(bot):
    bot.add_cog(Verification(bot))
