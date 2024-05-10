import asyncio
import discord
from discord.ext import commands
from discord.utils import format_dt
import datetime
from resources.database import add_show, delete_show, get_show


class EditEventModal(discord.ui.Modal):
    def __init__(self, event: discord.ScheduledEvent, original_message: discord.Message):
        super().__init__(timeout=None, title="Edit Event")
        self.event = event
        self.original_message = original_message
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.short, label="Show Number",
                      placeholder="Show Number", value=None, required=False))
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.short, label="Date",
                      placeholder="DD-MM", value=None, required=False))
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.short,
                      label="Time", placeholder="HH:MM", value=None, required=False))
        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.long,
                      label="Banner URL", placeholder="Banner URL", required=False))

    async def callback(self, interaction: discord.Interaction):
        show_number = self.children[0].value
        date = self.children[1].value
        time = self.children[2].value
        banner = self.children[3].value

        if not show_number and not date and not banner and not time:
            return await interaction.response.send_message("<:x_:1174507495914471464> You did not provide any information to update.", ephemeral=True)

        if show_number:
            await self.event.edit(name=f"INKIGAYO #{show_number}", reason=f"Updated by: {interaction.user.display_name}")
            embed = self.original_message.embeds[0]
            embed.title = f"INKIGAYO #{show_number}"
            await self.original_message.edit(embed=embed)

        if time and not date:
            date = date.split("-")
            day, month = self.event.start_time.day, self.event.start_time.month
            day = f"0{day}" if len(day) == 1 else day
            month = f"0{month}" if len(month) == 1 else month

            start_time = datetime.datetime.fromisoformat(
                f"2024-{month}-{day} {time}+00")
            await self.event.edit(start_time=start_time, reason=f"Updated by: {interaction.user.display_name}")
            embed = self.original_message.embeds[0]
            embed.set_field_at(0, name="<:time:987836664355373096> Date",
                               value=f"{format_dt(start_time, 'F')} ({format_dt(start_time, 'R')})")
            await self.original_message.edit(embed=embed)

        if date and not time:
            date = date.split("-")
            day, month = date[0], date[1]
            start_time = datetime.datetime.fromisoformat(
                f"2024-{month}-{day} {self.event.start_time.strftime('%H:%M:%S')}+00")
            await self.event.edit(start_time=start_time, reason=f"Updated by: {interaction.user.display_name}")
            embed = self.original_message.embeds[0]
            embed.set_field_at(0, name="<:time:987836664355373096> Date",
                               value=f"{format_dt(start_time, 'F')} ({format_dt(start_time, 'R')})")
            await self.original_message.edit(embed=embed)

        if date and time:
            date = date.split("-")
            day, month = date[0], date[1]
            start_time = datetime.datetime.fromisoformat(
                f"2024-{month}-{day} {time}+00")
            await self.event.edit(start_time=start_time, reason=f"Updated by: {interaction.user.display_name}")
            embed = self.original_message.embeds[0]
            embed.set_field_at(0, name="<:time:987836664355373096> Date",
                               value=f"{format_dt(start_time, 'F')} ({format_dt(start_time, 'R')})")
            await self.original_message.edit(embed=embed)

        if banner:
            embed = self.original_message.embeds[0]
            embed.set_image(url=banner)
            await self.original_message.edit(embed=embed)

        await interaction.response.send_message("<:checked:1173356058387951626> Successfully updated the event.", ephemeral=True)


class ManageView(discord.ui.View):
    def __init__(self, message: discord.Message, event: discord.ScheduledEvent):
        super().__init__(timeout=None)
        self.original_message = message
        self.event = event

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.green)
    async def start_event(self, button, interaction: discord.Interaction):
        if self.event.status == discord.ScheduledEventStatus.active:
            return await interaction.response.send_message("<:padlock:987837727741464666> This event is already active.", ephemeral=True)

        await interaction.response.defer()
        embed = self.original_message.embeds[0]
        fields = embed.fields

        fields[0].value = f"The show is starting!\n<:rightarrow:1173350998388002888> Join us in <#1178468708293808220>"
        fields[2].value = f"Link will be automatically provided **{format_dt(datetime.datetime.now() + datetime.timedelta(minutes=15), 'R')}**."
        embed.title = "Status: STARTING"

        await self.event.start(reason=f"Started by: {interaction.user.display_name}")
        await self.original_message.edit(embed=embed)
        await interaction.edit_original_response(content="<:checked:1173356058387951626> Successfully started the event.", view=None)
        s_message = await self.original_message.reply(content=f"<:notification:990034677836427295> **INKIGAYO** is starting soon! Join <#1178468708293808220>. Game link will be automatically provided **{format_dt(datetime.datetime.now() + datetime.timedelta(minutes=15), 'R')}**, @everyone.")

        await asyncio.sleep(60*15)
        await s_message.delete()
        fields[0].value = f"Happening now!\n<:rightarrow:1173350998388002888> Join us in <#1178468708293808220>"
        fields[2].value = "[Click Here](https://www.roblox.com/games/15522311097/INKIGAY0-ROBLOX)\n\n:warning: You **must be verified** with Sally to be able to **join** the Roblox game."
        embed.title = "Status: LIVE"
        await self.original_message.edit(embed=embed)
        await self.original_message.reply("<:link:986648044525199390> Game link is now **available**! Check the main message, @everyone.", mention_author=False, delete_after=60*20)

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
        embed.title = "Status: ENDED"

        if self.event.status == discord.ScheduledEventStatus.active:
            await self.event.complete(reason=f"Ended by: {interaction.user.display_name}")

        elif self.event.status == discord.ScheduledEventStatus.scheduled:
            await self.event.cancel(reason=f"Ended by: {interaction.user.display_name}")
            fields[0].value = "This event was cancelled."
            fields[2].value = "This event was cancelled."
            embed.title = "Status: CANCELLED"

        await self.original_message.edit(embed=embed, view=None)

        await delete_show(self.original_message.id)
        await interaction.edit_original_response(content="<:checked:1173356058387951626> Successfully ended the event.", view=None)

    @discord.ui.button(label="Edit Event", style=discord.ButtonStyle.gray)
    async def edit_event(self, button, interaction: discord.Interaction):
        await interaction.response.send_modal(EditEventModal(self.event, self.original_message))


class ShowView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Manage", emoji="<:editing:1174508480481218580>", style=discord.ButtonStyle.gray, custom_id="ManageEventButton")
    async def manage_event(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("<:padlock:987837727741464666> You can not manage this event.", ephemeral=True)

        original_message = interaction.message or await interaction.original_response()
        if original_message is None:
            return await interaction.response.send_message("<:x_:1174507495914471464> Something went wrong while fetching the message. Please try again.", ephemeral=True)

        show = await get_show(original_message.id)
        if show is None:
            return await interaction.response.send_message("<:x_:1174507495914471464> I could not find an event with this message.", ephemeral=True)

        event = interaction.guild.get_scheduled_event(show["event_id"]) or await interaction.guild.fetch_scheduled_event(show["event_id"])
        if event is None:
            await interaction.response.send_message("<:x_:1174507495914471464> The scheduled event was deleted. This show will be automatically deleted due to it becoming invalid.", ephemeral=True)
            await delete_show(original_message.id)
            embed = self.original_message.embeds[0]
            fields = embed.fields
            fields[0].value = "This event ended."
            fields[2].value = "This event ended."
            embed.title = "Status: ENDED"
            await original_message.edit(view=None)
            return

        view = ManageView(original_message, event)

        await interaction.response.send_message(view=view, ephemeral=True)


class Show(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ShowView())

    @commands.slash_command(description="Schedule and annonunce a show")
    async def show(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, show_number: discord.Option(str, "The show number"), date: discord.Option(str, "The date of the show. FORMAT: DD-MM"), time: discord.Option(str, "The time of the show in UTC TIME. FORMAT: HH:MM"), banner: discord.Option(str, "The banner of the show. Must be a link to an image.", default=None, required=False)):  # type: ignore
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.respond("<:padlock:987837727741464666> You are not allowed to use this command.", ephemeral=True)

        await ctx.defer()
        date = date.split("-")
        day, month = date[0], date[1]

        start_time = datetime.datetime.fromisoformat(
            f"2024-{month}-{day} {time}+00")

        embed = discord.Embed(color=discord.Color.nitro_pink(
        ), title=f"Status: SCHEDULED", description="**INKIGAYO** presents this week's show! Watch your favorite artists perform and vote for them.")

        embed.set_author(
            name=f"INKIGAYO #{show_number}", icon_url="https://cdn.discordapp.com/attachments/947298060646613032/1192273208699789492/spotlights.png")

        embed.add_field(name="<:time:987836664355373096> Date",
                        value=f"{format_dt(start_time, 'F')} ({format_dt(start_time, 'R')})")

        embed.add_field(name="<:thunderbolt:987447657104560229> VIP Benefits",
                        value=f"VIP members will be able to join the game **15 minutes** before the show starts and will be able to **skip the queue**. More perks and information in <#1179028774545784943>")

        embed.add_field(name="<:link:986648044525199390> Join the game",
                        value="The event has not started yet. Link will be provided when it starts.\n\n:warning: You **must be verified** with Sally to be able to **join** the Roblox game.")

        if banner:
            try:
                embed.set_image(url=banner)
            except:
                pass

        # For testing: 1015249782211616799 - INKIGAYO: 1178391939490517134
        announcements_channel = channel

        with open("src/resources/images/INKIGAYO-COVER.jpg", "rb") as image:
            event_image = image.read()

        # For testing: 1057393912588800100 - INKIGAYO: 1172515246615830609
        location = ctx.guild.get_channel(
            1178468708293808220) if ctx.guild.id == 1170821546038800464 else ctx.guild.get_channel(1057393912588800100)
        event = await ctx.guild.create_scheduled_event(name=f"INKIGAYO #{show_number}", description=f"INKIGAYO presents the week #{show_number} show. Watch your favorite artists perform, vote for them and give them a chance to win.", start_time=start_time, location=location, image=event_image, reason=f"Created by: {ctx.author.display_name}")
        message = await announcements_channel.send(content=f"@everyone [New INKIGAYO show!]({event.url})", embed=embed, view=ShowView())
        await add_show(message.id, event.id)
        await ctx.respond(content="<:checked:1173356058387951626> Successfully created this show.")


def setup(bot):
    bot.add_cog(Show(bot))
