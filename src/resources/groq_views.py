import discord
from discord.ui.input_text import InputText
import groq
from resources.aesthetic import Emojis


class FollowConversationModal(discord.ui.Modal):
    def __init__(self, groq_client, messages: list[dict], hidden: bool, *args, **kwargs):
        super().__init__(title="Continue Conversation", timeout=None, *args, **kwargs)
        self.messages = messages
        self.hidden = hidden
        self.groq_client: groq.AsyncGroq = groq_client
        self.add_item(InputText(style=discord.InputTextStyle.long,
                      label="Prompt", placeholder="Enter a prompt"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=self.hidden)
        messages = self.messages + \
            [{"role": "user", "content": self.children[0].value}]
        chat_completion = await self.groq_client.chat.completions.create(messages=messages, model="llama3-8b-8192", max_tokens=1024)
        response = chat_completion.choices[0].message.content

        new_messages = messages + [{"role": "system", "content": response}]
        formatted_response = f"{Emojis.user}: {self.children[0].value}\n{Emojis.sally}: {response}"
        await interaction.followup.send(content=formatted_response, view=FollowConversation(self.groq_client, new_messages, self.hidden), ephemeral=self.hidden)


class FollowConversation(discord.ui.View):
    def __init__(self, groq_client, messages: list[dict], hidden: bool):
        super().__init__(disable_on_timeout=True)
        self.messages = messages
        self.hidden = hidden
        self.groq_client = groq_client

    @discord.ui.button(label="Continue Conversation")
    async def callback(self, button, interaction: discord.Interaction):
        button.disabled = True
        modal = FollowConversationModal(
            self.groq_client, self.messages, self.hidden)
        await interaction.response.send_modal(modal)
        await interaction.edit_original_response(view=self)
