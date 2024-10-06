import discord
import lavalink
from config import emotes


class RemoveSongButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="<:delete:1055494235111034890>",
                         label="Remove Song", style=discord.ButtonStyle.gray, row=2)

    async def callback(self, interaction: discord.Interaction):
        player = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)
        queue = player.queue

        if len(queue) == 0:
            return await interaction.response.send_message(f"<:cross:1292282031216136254> There are no songs in the queue to remove!", ephemeral=True)

        songlist = queue[:25]

        options = []

        for index, song in enumerate(songlist):
            options.append(discord.SelectOption(
                label=song.title, description=f"By {song.author}", value=str(index), emoji="<:playlist:1005265606821548163>"))

        view = discord.ui.View(timeout=None)
        view.add_item(SongRemove(options))
        view.add_item(SongRemoveFromLast())
        await interaction.response.send_message(view=view, ephemeral=True)


class SongRemove(discord.ui.Select):
    def __init__(self, options: list, reversed: bool = False):
        super().__init__(placeholder="Select a song to remove")
        self.options = options
        self.reversed = reversed

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])

        player: lavalink.DefaultPlayer = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)

        if self.reversed:
            index = -index

        try:
            item = player.queue.pop(index)
            await interaction.response.edit_message(content=f"<:checked:1292282692536373318> Successfully removed `{item.title}`", view=None)

        except:
            await interaction.response.edit_message(content=f"<:cross:1292282031216136254> Something went wrong while removing the song. Try again.", view=None)


class SongRemoveFromLast(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Newest to oldest", emoji="<:repeat:1005256716050518216>")

    async def callback(self, interaction: discord.Interaction):
        player = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)
        queue = player.queue.copy()

        if len(queue) == 0:
            return await interaction.response.send_message(f"<:cross:1292282031216136254> There are no songs in the queue to remove!", ephemeral=True)

        queue.reverse()
        songlist = queue[:25]

        options = []

        for index, song in enumerate(songlist):
            options.append(discord.SelectOption(
                label=song.title, description=f"By {song.author}", value=str(index), emoji="<:playlist:1005265606821548163>"))

        view = discord.ui.View(timeout=None)
        view.add_item(SongRemove(options, True))
        await interaction.response.edit_message(content=f"<:Sally:1283499062389117068> Showing from newest additions to oldest", view=view)
