import discord
from discord.ui.input_text import InputText
import groq
from resources.aesthetic import Emojis


class DestroyConversation(discord.ui.View):
    def __init__(self, conversation_id: str):
        super().__init__(timeout=None)
        self.conversation_id = conversation_id

    @discord.ui.button(label="Stop Conversation", style=discord.ButtonStyle.grey, emoji="<:notalking:1283950338193489930>")
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)

        if self.conversation_id in interaction.client.ai_conversations.keys():
            interaction.client.ai_conversations.pop(self.conversation_id)
            return await interaction.followup.send(content=f"<:sad:1283952161109049355> The active conversation on this channel was stopped by {interaction.user}. No more messages will be prompted to the AI.")

        else:
            button.disabled = False
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(content=f"<:confused:1283952994710458390> Something went wrong while trying to stop the conversation on this channel. There is no conversation with this ID?", ephemeral=True)


class FollowConversationModal(discord.ui.Modal):
    def __init__(self, groq_client, messages: list[dict], hidden: bool, prefill: str = None, *args, **kwargs):
        super().__init__(title="Continue Conversation", timeout=None, *args, **kwargs)
        self.messages = messages
        self.hidden = hidden
        self.groq_client: groq.AsyncGroq = groq_client
        self.add_item(InputText(style=discord.InputTextStyle.long,
                      label="Prompt", placeholder="Enter a prompt", max_length=400, value=prefill))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=self.hidden, invisible=False)
        messages = self.messages + \
            [{"role": "user", "content": self.children[0].value}]
        chat_completion = await self.groq_client.chat.completions.create(messages=messages, model="llama3-70b-8192", max_tokens=350)
        response = chat_completion.choices[0].message.content

        new_messages = messages + [{"role": "system", "content": response}]
        formatted_response = f"<:response:1283501616800075816> {response}\n-# <:prompt:1283501054079799419> Prompt: {self.children[0].value} by {interaction.user.name} - Continued from previous conversation ({len(messages)} messages)"
        try:
            await interaction.followup.send(content=formatted_response, view=FollowConversation(self.groq_client, new_messages, self.hidden), ephemeral=self.hidden)
        except Exception as e:
            await interaction.followup.send(content=f"<:error:1283509705376923648> The response the model returned was somehow too big or something went wrong. You can continue the conversation or start a new one.\n-# <:prompt:1283501054079799419> Prompt: {self.children[0].value} by {interaction.user.name} - Continued from previous conversation ({len(messages)} messages)", view=FollowConversation(self.groq_client, new_messages, self.hidden, "Make your last answer shorter"), ephemeral=self.hidden)
            raise e

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        error = getattr(error, "original", error)
        if isinstance(error, groq.APIConnectionError):
            return await interaction.followup.send(content=f"<:error:1283509705376923648> The server to generate the response could not be reached. Please try again in a few minutes.", ephemeral=True)

        elif isinstance(error, groq.RateLimitError):
            return await interaction.followup.send(content=f"<:error:1283509705376923648> You are being ratelimited! Slow down and try again in a few minutes.", ephemeral=True)

        elif isinstance(error, groq.APIStatusError):
            return await interaction.followup.send(content=f"<:error:1283509705376923648> The server to generate the response returned an error. Please try again.", ephemeral=True)

        else:
            await interaction.followup.send(content=f"<:error:1283509705376923648> Something went wrong while generating the response. Please try again.")
        raise error


class FollowConversation(discord.ui.View):
    def __init__(self, groq_client, messages: list[dict], hidden: bool, prefill: str = None):
        super().__init__(disable_on_timeout=True)
        self.messages = messages
        self.hidden = hidden
        self.groq_client = groq_client
        self.prefill = prefill

    @discord.ui.button(label="Continue Conversation", style=discord.ButtonStyle.grey, emoji="<:response:1283501616800075816>")
    async def callback(self, button, interaction: discord.Interaction):
        button.disabled = True
        button.label = f"Continued by {interaction.user.name}"
        modal = FollowConversationModal(
            self.groq_client, self.messages, self.hidden, self.prefill)
        await interaction.response.send_modal(modal)
        await interaction.edit_original_response(view=self)
