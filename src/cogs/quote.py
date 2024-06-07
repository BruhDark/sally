import asyncio
import re

import discord
from discord.ext import commands


class ButtonDelete(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__(timeout=15.0)
        self.command = message

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.command.author != interaction.user:

            await interaction.response.send_message(content=f"aesthetic.Colors.secondary You can't use this button!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="​", emoji="🗑️", style=discord.ButtonStyle.danger, disabled=False)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.command.delete()
        await interaction.response.edit_message(view=None)


class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author != self.bot.user:

            pattern = re.compile(
                "https://(?:ptb.|canary.)?discord.com/channels/(?P<server_id>[0-9]{17,20})/(?P<channel_id>[0-9]{17,"
                "20})/(?P<message_id>[0-9]{17,20})")

            found = re.search(pattern, message.content)

            if found:

                msg_id = int(found.group('message_id'))
                server_id = int(found.group("server_id"))
                channel_id = int(found.group("channel_id"))

                if message.guild.id != server_id:
                    return

                msg = discord.utils.get(self.bot.cached_messages, id=msg_id)
                channel = message.guild.get_channel_or_thread(channel_id)
                msg = await channel.fetch_message(msg_id) if msg is None else msg

                if msg:
                    await message.add_reaction("📦")

                    def check(reaction, user):
                        return user == message.author and str(reaction.emoji) == "📦"

                    try:
                        await self.bot.wait_for("reaction_add", timeout=15.0, check=check)

                    except asyncio.TimeoutError:
                        await message.remove_reaction("📦", self.bot.user)

                    else:
                        await message.remove_reaction("📦", self.bot.user)
                        await message.remove_reaction("📦", message.author)

                        embed = discord.Embed(
                            title=f"Jump to message", url=f"https://discord.com/channels/{server_id}/{channel_id}/{msg_id}",
                            description=msg.content, color=aesthetic.Colors.main, timestamp=msg.created_at)
                        embed.set_author(
                            name=f"{msg.author} in {msg.channel}", icon_url=msg.author.display_avatar.url)
                        embed.set_footer(
                            text=f"Quoted by: {message.author}", icon_url=message.author.display_avatar.url)

                        view = ButtonDelete(message)
                        message = await message.channel.send(embed=embed)
                        view.message = message


def setup(bot):
    bot.add_cog(Quote(bot))
