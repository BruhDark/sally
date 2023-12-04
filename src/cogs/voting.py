import discord
from discord.ext import commands, pages
from discord.interactions import Interaction
import datetime
import time

from resources.database import create_poll, get_poll, add_vote, remove_vote, delete_poll
a = "▰▱"


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
                        print("default to 0")
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

        if time.time() - interaction.user.created_at.timestamp() <= 432000:
            return await interaction.followup.send(content="<:x_:1174507495914471464> Your account is too young. You are not allowed to vote.", ephemeral=True)

        original_message = await interaction.original_response() if interaction.message is None else interaction.message
        poll = await get_poll(original_message.id)
        user_choice = self.values[0]

        if poll is None:
            interaction.followup.send(
                "<:x_:1174507495914471464> This voting is invalid or something went wrong while fetching the information. Please contact a staff member.")

        try:
            if interaction.user.id in poll[f"{user_choice}_MEMBERS"]:
                new_data = await remove_vote(original_message.id, interaction.user.id, user_choice)
                new_embed = await self.return_new_embed(original_message, new_data)
                await original_message.edit(embed=new_embed)

                await interaction.followup.send(f"<:delete:1055494235111034890> Your vote for **{user_choice}** was removed.", ephemeral=True)

            else:
                for choice in poll["choices"]:
                    if interaction.user.id in poll[f"{choice}_MEMBERS"] and choice != user_choice:
                        return await interaction.followup.send(f"<:padlock:987837727741464666> You already voted for **{choice}**! You must remove your vote first if you want to vote for **{user_choice}**.", ephemeral=True)

                new_data = await add_vote(original_message.id, interaction.user.id, user_choice)
                new_embed = await self.return_new_embed(original_message, new_data)
                await original_message.edit(embed=new_embed)

                await interaction.followup.send(f"<:thunderbolt:987447657104560229> Your vote for **{user_choice}** was added successfully!", ephemeral=True)

        except Exception as ex:
            await interaction.followup.send("<:x_:1174507495914471464> Something went wrong while processing your vote. Please contact a staff member.")
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
        original_message = await interaction.original_response() if interaction.message is None else interaction.message
        poll = await get_poll(original_message.id)
        if poll == None:
            return await interaction.followup.send("<:x_:1174507495914471464> This voting is invalid or something went wrong.")

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
            await delete_poll(original_message.id)

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
        await delete_poll(original_message.id)

        await interaction.followup.send("<:checked:1173356058387951626> Ended poll and posted results.", ephemeral=True)


class Polls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PollView(None))

    @commands.slash_command(description="Create a groups voting")
    async def vote(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "The channel to send the voting"), group_1: discord.Option(str, "First group to add to the vote"), group_2: discord.Option(str, "Second group to add to the vote"), group_3: discord.Option(str, "Third group to add to the vote", default=None), group_4: discord.Option(str, "Fourth group to add to the vote", default=None), group_5: discord.Option(str, "Fifth group to add to the vote", default=None), group_6: discord.Option(str, "Sixth group to add to the vote", default=None)):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.repond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        await ctx.defer()
        groups = (group_1, group_2, group_3, group_4, group_5, group_6)
        groups_parsed = [group for group in groups if group != None]

        poll_embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:notification:990034677836427295> Voting Time!")
        poll_embed.description = "**INKIGAYO** presents this week group. Vote for your favorite group.\n\n<:info:881973831974154250> Only one vote is allowed per user."

        select_options = []
        for n, group in enumerate(groups_parsed):
            poll_embed.add_field(
                name=f"<:lyrics:1007803511028863066> Group #{n+1}: {group}", value="▱"*10 + " (0%)", inline=False)

            select_options.append(discord.SelectOption(
                label=group, value=group, description=f"Select this option to vote for {group} or to remove the vote.", emoji="<:lyrics:1007803511028863066>"))

        poll_embed.set_footer(
            text="Remove your vote by selecting the same option · INKIGAYO ROBLOX.", icon_url=ctx.guild.icon.url)

        poll_view = PollView(select_options)
        poll_message = await channel.send(content="@everyone", embed=poll_embed, view=poll_view)
        await create_poll(poll_message.id, groups_parsed)

        await ctx.respond("<:checked:1173356058387951626> Sent voting to channel.")

    @commands.slash_command(description="View the stats for a voting poll")
    async def view(self, ctx: discord.ApplicationContext, vote_id: discord.Option(str, "The ID of the vote. (Message ID)")):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.repond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        try:
            poll = await get_poll(int(vote_id))
        except ValueError:
            return await ctx.respond("<:x_:1174507495914471464> Invalid voting ID.", ephemeral=True)

        if poll == None:
            return await ctx.respond("<:x_:1174507495914471464> No voting found with this ID.", ephemeral=True)

        embeds = []
        main_embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:elections:1173351008655642756> Voting Stats")
        main_embed.add_field(
            name="<:rightarrow:1173350998388002888> Message", value=f"https://discord.com/channels/1170821546038800464/1171604109720297512/{vote_id}", inline=False)

        main_embed.add_field(
            name="<:rightarrow:1173350998388002888> Total Votes", value=str(poll["total_votes"]), inline=False)
        for choice in poll["choices"]:
            main_embed.add_field(
                name=f"<:vinyl:1173351007263133756> {choice} votes", value=str(poll[choice]))

            users = [await self.bot.get_or_fetch_user(user)
                     for user in poll[choice+"_MEMBERS"]]
            choice_embed = discord.Embed(color=discord.Color.purple(
            ), title=f"<:elections:1173351008655642756> Users that voted for {choice}")

            users_parsed = [
                f"{user.mention} ({user.display_name})" for user in users]
            choice_embed.description = "\n".join(users_parsed)
            choice_embed.set_footer(
                text=f"{poll[choice]} total votes for {choice}", icon_url=ctx.guild.icon.url)

            embeds.append(choice_embed)

        embeds[0:0] += [main_embed]

        paginator = pages.Paginator(
            pages=embeds, show_disabled=False, author_check=True, disable_on_timeout=True)
        await paginator.respond(ctx.interaction)


def setup(bot):
    bot.add_cog(Polls(bot))
