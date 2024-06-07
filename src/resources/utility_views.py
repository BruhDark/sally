import discord
import aesthetic


class ConfirmActionView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.confirmed = False

    async def on_timeout(self) -> None:
        await self.message.edit(content=f"{aesthetic.Emojis.error} This action was automatically cancelled, you took too long to respond.", view=None)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.confirmed = True
        await interaction.response.edit_message(content="You confirmed this action.", view=None)
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"{aesthetic.Emojis.error} You cancelled this action.", view=None)
        self.stop()
