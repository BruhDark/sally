import asyncio
import discord
from discord.ext import commands
from discord.utils import format_dt
import datetime
from resources.database import add_show, delete_show, get_show


class ManageView(discord.ui.View):
    def __init__(self, message: discord.Message, event: discord.ScheduledEvent):
        super().__init__(timeout=None)
        self.original_message = message
        self.event = event
        if event.status == discord.ScheduledEventStatus.active:
            self.start_event.disabled = True

        elif event.status == discord.ScheduledEventStatus.scheduled:
            self.end_event.label = "Cancel Event"

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.green)
    async def start_event(self, button, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = self.original_message.embeds[0]
        fields = embed.fields

        fields[0].value = f"LIVE **NOW**!\n<:rightarrow:1173350998388002888> Join us in {self.event.location.value.mention}"
        fields[2].value = f"Link will be automatically provided **{format_dt(datetime.datetime.now() + datetime.timedelta(minutes=15), 'R')}**."
        embed.title += " - LIVE NOW"

        await self.event.start(reason=f"Started by: {interaction.user.display_name}")
        await self.original_message.edit(embed=embed)
        await interaction.edit_original_response(content="<:checked:1173356058387951626> Successfully started the event.", view=None)

        await asyncio.sleep(60*15)
        fields[2].value = "[Click Here](https://www.roblox.com/games/15280036840/INKIGAYO-ROBLOX)"
        await self.original_message.edit(embed=embed)
        await self.original_message.reply("<:link:986648044525199390> Game link is now **available**.", mention_author=False)
        await self.original_message.channel.send("@here", delete_after=1)

    @discord.ui.button(label="End Event", style=discord.ButtonStyle.red)
    async def end_event(self, button, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = self.original_message.embeds[0]
        fields = embed.fields
        if "automatically provided" in fields[2].value:
            tm = fields[2].value.split(" ")[-1]
            return await interaction.edit_original_response(content=f"<:padlock:987837727741464666> Can not cancel event with on-going countdown for game link. Try again {tm}", view=None)

        fields[0].value = "This event ended."
        fields[2].value = "This event ended."
        embed.title = embed.title.replace("LIVE NOW", "ENDED")

        if self.event.status == discord.ScheduledEventStatus.active:
            await self.event.complete(reason=f"Ended by: {interaction.user.display_name}")

        else:
            await self.event.cancel(reason=f"Ended by: {interaction.user.display_name}")
            fields[0].value = "This event was cancelled."
            fields[2].value = "This event was cancelled."
            embed.title += " - CANCELLED"

        await self.original_message.edit(embed=embed, view=None)

        await delete_show(self.original_message.id)
        await interaction.edit_original_response(content="<:checked:1173356058387951626> Successfully ended the event.", view=None)


class ShowView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Manage", emoji="<:editing:1174508480481218580>", style=discord.ButtonStyle.gray, custom_id="ManageEventButton")
    async def manage_event(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("<:padlock:987837727741464666> You can not manage this event.", ephemeral=True)

        original_message = await interaction.original_response() if interaction.message == None else interaction.message

        show = await get_show(original_message.id)
        if show is None:
            return await interaction.response.send_message("<:x_:1174507495914471464> This show is invalid.", ephemeral=True)

        event = interaction.guild.get_scheduled_event(show["event_id"])
        if event is None:
            await interaction.response.send_message("<:x_:1174507495914471464> The scheduled event was deleted. This show will be automatically deleted due to it becoming invalid.", ephemeral=True)
            await delete_show(original_message.id)
            await original_message.edit(view=None)

        view = ManageView(original_message, event)

        await interaction.response.send_message(view=view, ephemeral=True)


class Show(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ShowView())

    @commands.slash_command(description="Schedule and annonunce a show", guild_ids=[881968885279117342, 1170821546038800464])
    async def show(self, ctx: discord.ApplicationContext, show_number: discord.Option(str, "The show number"), date: discord.Option(str, "The date of the show. FORMAT: DD-MM"), time: discord.Option(str, "The time of the show in UTC TIME. FORMAT: HH:MM")):
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.respond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        await ctx.defer()
        date = date.split("-")
        day, month = date[0], date[1]

        start_time = datetime.datetime.fromisoformat(
            f"2023-{month}-{day} {time}+00")

        embed = discord.Embed(color=discord.Color.nitro_pink(
        ), title=f"<:spotlights:1173351002196422737> INKIGAYO WEEK {show_number}", description="**INKIGAYO** presents this week's show! Watch your favorite artists perform and vote for them.")

        embed.add_field(name="<:time:987836664355373096> Date",
                        value=f"{format_dt(start_time, 'F')} ({format_dt(start_time, 'R')})")

        embed.add_field(name="<:elections:1173351008655642756> Vote",
                        value=f"Vote for your favorite artist/group in <#1171604109720297512> and give them a chance to win this week!")

        embed.add_field(name="<:link:986648044525199390> Join the game",
                        value="The event has not started yet. Link will be provided when it starts.")

        # For testing: 1015249782211616799 - INKIGAYO: 1170851944055705700
        announcements_channel = ctx.guild.get_channel(1170851944055705700)

        with open("src/resources/images/INKIGAYO-COVER.jpg", "rb") as image:
            event_image = image.read()

        # For testing: 1057393912588800100 - INKIGAYO: 1172515246615830609
        event = await ctx.guild.create_scheduled_event(name=f"INKIGAYO SHOW #{show_number}", description=f"INKIGAYO presents the week #{show_number} show. Watch your favorite artists perform and vote for them to give them a chance to win.", start_time=start_time, location=ctx.guild.get_channel(1172515246615830609), image=event_image, reason=f"Created by: {ctx.author.display_name}")
        message = await announcements_channel.send(content=f"@everyone [New show!]({event.url})", embed=embed, view=ShowView())
        await add_show(message.id, event.id)
        await ctx.respond(content="<:checked:1173356058387951626> Successfully created this show.")


def setup(bot):
    bot.add_cog(Show(bot))
