import discord
from discord.ext import commands, pages
from discord.interactions import Interaction
from resources.utility_views import ConfirmActionView
from resources import database as db
import time
# ▰▱


class PollSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(options=options, custom_id="PollSelect", placeholder="Select an artist")

    async def return_new_embed(self, message: discord.Message, poll: dict):
        embed = message.embeds[0]
        fields = embed.fields
        total = poll["total_votes"]

        for choice in poll["choices"]:
            for field in fields:
                if choice in field.name:
                    if total == 0:
                        percentage = 0

                    else:
                        percentage = (poll[choice] / total) * 100

                    squares = ""
                    squares += "▱" * (10 - int(percentage) // 10)
                    squares = squares.rjust(10, "▰")

                    field.value = f"{squares} ({round(percentage, 2)}%)"
                    break

        return embed

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        verified_role = discord.utils.get(
            interaction.guild.roles, name="Verified")
        if verified_role not in interaction.user.roles:
            return await interaction.followup.send(content="<:x_:1174507495914471464> You must be verified to vote. Please use </verify:1183583727473917962> in a channel.", ephemeral=True)

        if time.time() - interaction.user.created_at.timestamp() <= 432000:
            return await interaction.followup.send(content="<:x_:1174507495914471464> Your account is too young. You are not allowed to vote.", ephemeral=True)

        original_message = await interaction.original_response() if interaction.message is None else interaction.message
        poll = await db.get_poll(original_message.id)
        user_choice = self.values[0]

        if poll is None:
            interaction.followup.send(
                "<:x_:1174507495914471464> This voting is invalid or something went wrong while fetching the information. Please contact a staff member.")

        try:
            if interaction.user.id in poll[f"{user_choice}_MEMBERS"]:
                new_data = await db.remove_vote(original_message.id, interaction.user.id, user_choice)
                new_embed = await self.return_new_embed(original_message, new_data)
                await original_message.edit(embed=new_embed)

                await interaction.followup.send(f"<:delete:1055494235111034890> Your vote for **{user_choice}** was removed.", ephemeral=True)

            else:
                for choice in poll["choices"]:
                    if interaction.user.id in poll[f"{choice}_MEMBERS"] and choice != user_choice:
                        return await interaction.followup.send(f"<:padlock:987837727741464666> You already voted for **{choice}**! You must remove your vote first if you want to vote for **{user_choice}**.", ephemeral=True)

                new_data = await db.add_vote(original_message.id, interaction.user.id, user_choice)
                new_embed = await self.return_new_embed(original_message, new_data)
                await original_message.edit(embed=new_embed)

                await interaction.followup.send(f"<:thunderbolt:987447657104560229> Your vote for **{user_choice}** was added successfully!", ephemeral=True)

        except Exception as ex:
            await interaction.followup.send("<:x_:1174507495914471464> Something went wrong while processing your vote. Please try again or contact a staff member.", ephemeral=True)
            raise ex


class PollView(discord.ui.View):
    def __init__(self, select_options):
        super().__init__(timeout=None)
        self.add_item(PollSelect(select_options))

    @discord.ui.button(style=discord.ButtonStyle.red, label="End Voting", custom_id="EndVoting", row=1)
    async def end_voting(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("<:padlock:987837727741464666> You are not allowed to use this button.", ephemeral=True)
            return

        await interaction.response.defer()
        view = ConfirmActionView()
        await interaction.followup.send("Are you sure you want to end this voting?", ephemeral=True, view=view)
        await view.wait()

        if not view.confirmed:
            return

        original_message = await interaction.original_response() if interaction.message is None else interaction.message
        poll = await db.get_poll(original_message.id)
        if poll == None:
            return await interaction.followup.send("<:x_:1174507495914471464> This voting is invalid or something went wrong.", ephemeral=True)

        if poll["total_votes"] == 0:
            embed = original_message.embeds[0]
            embed.clear_fields()
            embed.title = "<:notification:990034677836427295> Voting time ended!"
            embed.description = f"**INKIGAYO** presents the **winner** of this week group!\n\nBetween the {len(poll['choices'])} groups of this week (**{', '.join(poll['choices'])}**) the winner is:"
            embed.set_footer(
                text=f"{poll['total_votes']} total votes · Ended by {interaction.user.display_name}", icon_url=interaction.guild.icon.url)

            embed.add_field(name=f"No winner was determined",
                            value=f"The total votes count was 0")

            await original_message.edit(embed=embed, view=None)
            await db.delete_poll(original_message.id)

            await interaction.followup.send("<:checked:1173356058387951626> Ended the voting and posted results.", ephemeral=True)
            return

        may = None
        may_n = 0
        tie = False
        tie_name = None

        for n, choice in enumerate(poll["choices"]):
            if poll[choice] > may_n:
                may = choice
                may_n = poll[choice]

            elif poll[choice] == may_n and n+1 == len(poll["choices"]):
                tie = True
                tie_name = choice

        embed = original_message.embeds[0]
        embed.clear_fields()
        embed.title = "<:notification:990034677836427295> Voting time ended!"
        embed.description = f"**INKIGAYO** presents the **winner** group of this week!\n\nBetween the {len(poll['choices'])} groups of this week (**{', '.join(poll['choices'])}**) the winner is:"
        embed.set_footer(
            text=f"{poll['total_votes']} total votes · Ended by {interaction.user.display_name}", icon_url=interaction.guild.icon.url)
        if tie:
            embed.add_field(name="<:help:988166431109681214> Tie",
                            value=f"There was a tie between **{may}** and **{tie_name}**!")
        else:
            embed.add_field(name=f"<:trophy:1173351004310351954> {may}",
                            value=f"**{may}** wins with **{may_n}** votes!")

        await original_message.edit(embed=embed, view=None)
        await db.delete_poll(original_message.id)

        await interaction.followup.send("<:checked:1173356058387951626> Ended poll and posted results.", ephemeral=True)


class Polls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PollView(None))

    voting = discord.SlashCommandGroup(
        name="voting", description="Commands to create and manage votings")

    @voting.command(description="Create a voting poll")
    @discord.default_permissions(manage_server=True)
    async def create(self, ctx: discord.ApplicationContext, poll_id: discord.Option(str, "A unique ID for this poll"), group_1: discord.Option(str, "First group to add to the vote"), group_2: discord.Option(str, "Second group to add to the vote"), group_3: discord.Option(str, "Third group to add to the vote", default=None), group_4: discord.Option(str, "Fourth group to add to the vote", default=None), group_5: discord.Option(str, "Fifth group to add to the vote", default=None), group_6: discord.Option(str, "Sixth group to add to the vote", default=None)):  # type: ignore
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.repond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        await ctx.defer()
        groups = (group_1, group_2, group_3, group_4, group_5, group_6)
        groups_parsed = [group for group in groups if group != None]

        if await db.get_poll(poll_id) != None:
            return await ctx.respond("<:x_:1174507495914471464> A voting with this ID already exists.", ephemeral=True)

        poll_embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="Successfully created this voting poll!")

        poll_embed.description = "The poll is created as inactive. You can activate it by using the `/voting status` command. Otherwise it will not be visible on the game."

        poll_embed.add_field(name="Poll ID", value=poll_id)
        poll_embed.add_field(name="Poll status", value="Inactive")
        poll_embed.add_field(name="Groups", value=", ".join(groups_parsed))

        await db.create_poll(poll_id, groups_parsed)
        await ctx.respond(embed=poll_embed)

    @voting.command(description="Change the status of a poll")
    @discord.default_permissions(manage_server=True)
    @discord.option(name="poll_id", description="The poll ID", type=str)
    @discord.option(name="status", description="The status to set", type=str, choices=["active", "inactive"])
    async def status(self, ctx, poll_id: str, status: str):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.repond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        poll = await db.get_poll(poll_id)
        if poll == None:
            return await ctx.respond("<:x_:1174507495914471464> No voting found with this ID.", ephemeral=True)

        a_poll = await db.get_active_poll()
        if a_poll != None:
            return await ctx.respond(f"<:x_:1174507495914471464> There is already an active voting (`{poll['_id']}`). You must change its status first.", ephemeral=True)

        if status == "active":
            await db.change_poll_status(poll_id, "ACTIVE")
            await ctx.respond(f"<:checked:1173356058387951626> Voting `{poll_id}` is now active.")

        elif status == "inactive":
            await db.change_poll_status(poll_id, "INACTIVE")
            await ctx.respond(f"<:checked:1173356058387951626> Voting `{poll_id}` is now inactive.")

    @voting.command(description="View the stats for a voting poll")
    @discord.default_permissions(manage_server=True)
    async def view(self, ctx: discord.ApplicationContext, vote_id: discord.Option(str, "The poll ID")):  # type: ignore
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.repond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        try:
            poll = await db.get_poll(vote_id)
        except ValueError:
            return await ctx.respond("<:x_:1174507495914471464> Invalid voting ID.", ephemeral=True)

        if poll == None:
            return await ctx.respond("<:x_:1174507495914471464> No voting found with this ID.", ephemeral=True)

        main_embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:elections:1173351008655642756> Voting Stats")

        main_embed.add_field(
            name="<:rightarrow:1173350998388002888> Total Votes", value=str(poll["total_votes"]), inline=False)
        for choice in poll["choices"]:
            main_embed.add_field(
                name=f"<:vinyl:1173351007263133756> {choice} votes", value=str(poll[choice]))

        await ctx.respond(embed=main_embed)


def setup(bot):
    bot.add_cog(Polls(bot))
