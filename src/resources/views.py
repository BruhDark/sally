import discord
from discord.interactions import Interaction
from resources.database import get_date, edit_date, return_dates

import asyncio

class SelectDateDropdown(discord.ui.Select):
    def __init__(self, options: list, buyer: discord.Member, users: list, tickets_amount: int,):
        super().__init__(options=options, placeholder="Selecciona una fecha")
        self.buyer: discord.Member = buyer
        self.users_ids = users
        self.tickets_amount = int(tickets_amount)

    async def callback(self, interaction: Interaction):

        await interaction.response.defer()

        date = await get_date(self.values[0])
        if not date:
            return await interaction.followup.send(content="🛑 Ups! Algo salió mal internamente. No puedo acceder a la fecha seleccionada.")

        if date["tickets_available"] > 0 and date["tickets_available"] > self.tickets_amount:
            users = [interaction.guild.get_member(int(user)) for user in self.users_ids]
            role = interaction.guild.get_role(int(date["role"]))
            for user in users:
                await user.add_roles(role)

            await self.buyer.send(content=f"🎉 Tus tickets han sido aprobados y tus roles han sido asignados. Tu fecha asignada: **{date['date']}**")
            await self.buyer.send(content="🔦 Si no ves tus roles, puede que haya habido un error. Contacta al staff.")
            
            await interaction.followup.send(content="🪄 Hecho! Roles asignados y usuario notificado.")

            await edit_date(self.values[0], {"tickets_sold": date["tickets_sold"] + self.tickets_amount, "tickets_available": date["tickets_available"] - self.tickets_amount})

            message = await interaction.original_response()
            embed = message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "🗳 Ticket aprobado!"

            await message.edit(embed=embed, view=None)
            self.view.stop()

        else:
            await interaction.followup.send(content="⚠️ Ya no hay tickets disponibles o la cantidad de tickets a comprar es mayor que la de los disponibles. Selecciona otra fecha.")


class ApproveDenyTicketView(discord.ui.View):
    def __init__(self, buyer: discord.Member, users: list, tickets_amount: int, date_options: list):
        super().__init__(timeout=None)
        self.buyer = buyer
        self.add_item(SelectDateDropdown(date_options, buyer, users, tickets_amount))

    @discord.ui.button(label="Denegar Ticket", emoji="❌", style=discord.ButtonStyle.red)
    async def callback(self, button, interaction):
        self.disable_all_items()
        
        await self.buyer.send(content="🚷 Tu ticket ha sido denegado. Deberás entrar a la fila de nuevo si deseas intentar comprar de nuevo los tickets.")
        await interaction.response.send_message(content="🪄 Hecho! El ticket ha sido denegado y he notificado al usuario.")

        embed = self.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Ticket denegado"
        await self.message.edit(embed=embed, view=self)

        self.stop()

class ProcessTicketView(discord.ui.View):
    def __init__(self, message):
        super().__init__(timeout=60*10)
        self.intern_message = message
        self.submitted = False
        self.decided = False
        self.timed_out = False

    async def on_timeout(self):
        self.disable_all_items()
        self.timed_out = True
        embed = discord.Embed(color=discord.Color.red(), description="Haz alcanzado tu tiempo limite! Tu compra ha sido cancelada.")
        await self.message.edit(content=None, embed=embed, view=self)

    @discord.ui.button(label="Comprar Ticket", emoji="🎫", style=discord.ButtonStyle.blurple)
    async def buy_ticket_callback(self, button: discord.ui.Button, interaction: discord.Interaction):

        await interaction.response.send_message(content=":wave: Hola! Estas a un solo paso de poder comprar tus tickets. Te recuerdo que solo tienes **10 minutos** para comprar tus tickets, o tu compra será cancelada.\nYa deberías tener todos tus datos a la mano! Solo deberías seguir las instrucciones.")
        await asyncio.sleep(3)
        await interaction.followup.send(content="🛍️ ¿Cuantos tickets deseas comprar? **Solo** dí el número de tickets.")

        def amount_check(message: discord.Message):
            return message.content.isdigit() and message.author.id == interaction.user.id and message.channel.id == interaction.channel.id
        
        tickets_amount = await interaction.client.wait_for("message", check=amount_check)

        if not tickets_amount.content.isdigit():
            await interaction.channel.send(content="🛑 Tus tickets han sido rechazados. Cantidad de boletos inválida. Deberás entrar de nuevo a la fila para conseguir nuevos tickets.")
            self.stop()
            return
        
        if self.timed_out: return

        await interaction.channel.send(content="🪪 Por favor provee las ID de usuarios de Discord de las personas que recibiran el ticket. **Deben estar separadoras por una coma (en caso de ser más de una)**. Por ejemplo: `12345, 678910`\n¿No sabes como obtener las ID? Haz [click aquí](https://support.discord.com/hc/es/articles/206346498) para saber como encontrar tu o las IDs de tus amigos.")
        
        def users_check(message):
            return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id
        
        user_ids = await interaction.client.wait_for("message", check=users_check)

        if self.timed_out: return

        await interaction.channel.send(content="🔗 Por favor provee los usuarios de Roblox de las personas que recibiran el ticket. **Deben estar separados por una coma (en caso de ser más de una)**. Por ejemplo: `DarkPxint, RobloxUser`")
        
        roblox_users = await interaction.client.wait_for("message", check=users_check)

        if self.timed_out: return

        user_ids = user_ids.content.split(",")
        
        try:
            users = [await interaction.client.get_or_fetch_user(int(user)) for user in user_ids]
        except ValueError:
            await interaction.channel.send(content="🛑 Tus tickets han sido rechazados. Hay IDs de usuarios de Discord inválidas! Deberás entrar de nuevo a la fila para conseguir nuevos tickets.")
            self.stop()
            return

        if None in users:
            await interaction.channel.send(content="🛑 Tus tickets han sido rechazados. Hay IDs de usuarios de Discord inválidas! Deberás entrar de nuevo a la fila para conseguir nuevos tickets.")
            self.stop()
            return
        

        users_parsed = [user.mention for user in users]

        info_embed = discord.Embed(color=discord.Color.blurple())
        info_embed.set_author(name=f"Comprador: {interaction.user}", icon_url=interaction.user.display_avatar.url)

        info_embed.add_field(name="💳 Cantidad de tickets a comprar", value=tickets_amount.content, inline=False)
        info_embed.add_field(name="🪪 Usuario(s)", value=" ".join(users_parsed), inline=False)
        info_embed.add_field(name="🔗 Usuario(s) de Roblox", value=roblox_users.content, inline=False)

        dates = await return_dates()
        select_options = []
        for date in dates:
            select_options.append(discord.SelectOption(label=f"{date['date']} - Disponibles: {date['tickets_available']}", value=date["date_id"],
                                                       description=f"Tickets totales: {date['tickets_amount']}, Tickets vendidos: {date['tickets_sold']}"))

        approve_tickets = ApproveDenyTicketView(interaction.user, user_ids, tickets_amount.content, select_options)
        await self.intern_message.edit(embed=info_embed, view=approve_tickets)

        await interaction.channel.send("🚀 Gracias! Tu ticket(s) han sido enviado a revisión. Te avisaremos de su estado!")
        self.submitted = True
        if not await approve_tickets.wait():
            self.decided = True
            self.stop()




