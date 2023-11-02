import discord
from discord.interactions import Interaction
from resources.database import get_date, edit_date, return_dates

import asyncio


class SelectDateDropdown(discord.ui.Select):

  def __init__(
    self,
    options: list,
    buyer: discord.Member,
    users: list,
    tickets_amount: int,
  ):
    super().__init__(options=options, placeholder="Selecciona una fecha")
    self.buyer: discord.Member = buyer
    self.users_ids = users
    self.tickets_amount = int(tickets_amount)

  async def callback(self, interaction: Interaction):

    await interaction.response.defer()
    if self.values[0] == "Invalid":
      return await interaction.followup.send(
        "No es posible seleccionar este valor.")

    date = await get_date(self.values[0])
    if not date:
      return await interaction.followup.send(
        content=
        "🛑 Ups! Algo salió mal internamente. No puedo acceder a la fecha seleccionada."
      )

    if date["tickets_available"] > 0 and date[
        "tickets_available"] >= self.tickets_amount:
      users = [
        interaction.guild.get_member(int(user)) for user in self.users_ids
      ]
      success_add = []
      failed_add = []
      role = interaction.guild.get_role(int(date["role"]))
      for user in users:
        try:
          await user.add_roles(role)
          success_add.append(user.mention)
        except:
          if user is not None:
            failed_add.append(user.mention)
          else:
            failed_add.append(
              f"<@{str(self.users_ids[users.index(user)]).strip()}>")

      if len(failed_add) == 0:
        failed_add = ["Ninguno"]

      roles_embed = discord.Embed(color=discord.Color.blurple())
      roles_embed.add_field(name="🎉 Personas añadidas al rol correctamente",
                            value=", ".join(success_add))
      roles_embed.add_field(
        name="‼️ Personas a las que no pude añadirles el rol",
        value=", ".join(failed_add))

      await self.buyer.send(
        content=
        f"🎉 Tus tickets han sido aprobados y tus roles han sido asignados. Tu fecha asignada: **{date['date']}**\n🔦 Si no ves tus roles, puede que haya habido un error. Contacta al staff.",
        embed=roles_embed)

      await interaction.followup.send(
        content="🪄 Hecho! Roles asignados y usuario notificado.",
        embed=roles_embed)
      if len(failed_add) > 0:
        await interaction.channel.send(
          content=
          "ℹ️ Una falla en la asignación en los roles puede ser causada por falta de permisos o los usuarios no están en el servidor."
        )

      await edit_date(
        self.values[0], {
          "tickets_sold": date["tickets_sold"] + self.tickets_amount,
          "tickets_available": date["tickets_available"] - self.tickets_amount
        })

      message = await interaction.original_response()
      embed = message.embeds[0]
      embed.color = discord.Color.green()
      embed.title = "🗳 Ticket aprobado!"

      await message.edit(embed=embed, view=None)
      self.view.stop()

    else:
      await interaction.followup.send(
        content=
        "⚠️ Ya no hay tickets disponibles o la cantidad de tickets a comprar es mayor que la de los disponibles. Selecciona otra fecha."
      )


class ApproveDenyTicketView(discord.ui.View):

  def __init__(self, buyer: discord.Member, users: list, tickets_amount: int,
               date_options: list):
    super().__init__(timeout=None)
    self.buyer = buyer
    self.add_item(
      SelectDateDropdown(date_options, buyer, users, tickets_amount))

  @discord.ui.button(label="Denegar Ticket",
                     emoji="❌",
                     style=discord.ButtonStyle.red)
  async def callback(self, button, interaction):
    self.disable_all_items()

    await self.buyer.send(
      content=
      "🚷 Tus tickets han sido denegados por el staff.\nDeberás entrar a la fila de nuevo si deseas intentar comprar de nuevo los tickets.\n\nℹ️ Los motivos del rechazo de tus tickets pueden variar! Es probable que ya tengas un ticket para otra fecha y que no puedas acumular más fechas, que no haya disponibilidad de fechas, o que los datos proporcionados no sean correctos/no coincidan."
    )

    await interaction.response.edit_message(view=self)

    await interaction.followup.send(
      content="🪄 Hecho! El ticket ha sido denegado y he notificado al usuario."
    )

    self.stop()


class ProcessTicketView(discord.ui.View):

  def __init__(self, message, guild_id: int):
    super().__init__(timeout=60 * 3)
    self.intern_message = message
    self.submitted = False
    self.decided = False
    self.timed_out = False
    self.guild_id = guild_id
    self.cancelled = False

  async def on_timeout(self):
    self.disable_all_items()
    self.timed_out = True
    embed = discord.Embed(
      color=discord.Color.red(),
      description="Has alcanzado tu tiempo limite! Tu compra ha sido cancelada."
    )
    await self.message.edit(content=None, embed=embed, view=self)

  @discord.ui.button(label="Comprar Ticket",
                     emoji="🎫",
                     style=discord.ButtonStyle.blurple)
  async def buy_ticket_callback(self, button: discord.ui.Button,
                                interaction: discord.Interaction):

    await interaction.response.send_message(
      content=
      ":wave: Hola! Estas a un solo paso de poder comprar tus tickets. Te recuerdo que solo tienes **3 minutos** para comprar tus tickets, o tu compra será cancelada.\nYa deberías tener todos tus datos a la mano! Solo deberías seguir las instrucciones."
    )
    await interaction.followup.send(
      content=
      "🛍️ ¿Cuantos tickets deseas comprar? **Solo** dí el número de tickets.")

    def amount_check(message: discord.Message):
      return message.content.isdigit(
      ) and message.author.id == interaction.user.id and message.channel.id == interaction.channel.id

    tickets_amount = await interaction.client.wait_for("message",
                                                       check=amount_check)

    if not tickets_amount.content.isdigit():
      await interaction.channel.send(
        content=
        "🛑 Tus tickets han sido rechazados automáticamente. Cantidad de boletos inválida. Deberás entrar de nuevo a la fila para conseguir nuevos tickets."
      )
      self.stop()
      return

    if self.timed_out: return

    await interaction.channel.send(
      content=
      "🪪 Por favor provee las IDs de usuarios de Discord de las personas que recibiran el ticket.\n**Deben estar separadoras por una coma (en caso de ser más de una)**. Por ejemplo: `12345, 678910`\n\n¿No sabes como obtener las ID? Haz revisa este artículo: <https://support.discord.com/hc/es/articles/206346498> para saber como encontrar las IDs necesarias."
    )

    def users_check(message):
      return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id

    user_ids = await interaction.client.wait_for("message", check=users_check)

    if self.timed_out: return

    await interaction.channel.send(
      content=
      "🔗 Por favor provee los usuarios de Roblox de las personas que recibiran el ticket.\n**Deben estar separados por una coma (en caso de ser más de uno)**. Por ejemplo: `DarkPxint, RobloxUser`"
    )

    roblox_users = await interaction.client.wait_for("message",
                                                     check=users_check)

    if self.timed_out: return

    user_ids = user_ids.content.split(",")

    try:
      users = [
        await interaction.client.get_or_fetch_user(int(user))
        for user in user_ids
      ]
    except ValueError:
      await interaction.channel.send(
        content=
        "🛑 Tus tickets han sido rechazados **automáticamente**. Hay IDs de usuarios de Discord inválidas! Deberás entrar de nuevo a la fila para conseguir nuevos tickets."
      )
      self.stop()
      return

    if None in users:
      await interaction.channel.send(
        content=
        "🛑 Tus tickets han sido rechazados **automáticamente**. Hay IDs de usuarios de Discord inválidas! Deberás entrar de nuevo a la fila para conseguir nuevos tickets."
      )
      self.stop()
      return

    users_parsed = [user.mention for user in users]

    info_embed = discord.Embed(color=discord.Color.blurple())
    info_embed.set_author(name=f"Comprador: {interaction.user}",
                          icon_url=interaction.user.display_avatar.url)

    info_embed.add_field(name="💳 Cantidad de tickets a comprar",
                         value=tickets_amount.content,
                         inline=False)
    info_embed.add_field(name="🪪 Usuario(s)",
                         value=" ".join(users_parsed),
                         inline=False)
    info_embed.add_field(name="🔗 Usuario(s) de Roblox",
                         value=roblox_users.content,
                         inline=False)

    dates = await return_dates(self.guild_id)
    select_options = []
    for date in dates:
      if date['tickets_available'] > 0:
        select_options.append(
          discord.SelectOption(
            label=f"{date['date']} - Disponibles: {date['tickets_available']}",
            value=date["date_id"],
            description=
            f"Tickets totales: {date['tickets_amount']}, Tickets vendidos: {date['tickets_sold']}"
          ))

    if len(select_options) == 0:
      select_options.append(
        discord.SelectOption(label="No hay fechas disponibles",
                             value="Invalid"))
    approve_tickets = ApproveDenyTicketView(interaction.user, user_ids,
                                            tickets_amount.content,
                                            select_options)
    await self.intern_message.edit(embed=info_embed, view=approve_tickets)

    await interaction.channel.send(
      "🐶 Gracias! Tus tickets han sido enviados a revisión. Recibirás un nuevo mensaje cuando sean aprobados o denegados."
    )
    self.submitted = True
    if not await approve_tickets.wait():
      self.decided = True
      self.stop()

  @discord.ui.button(label="Cancelar compra", emoji="🛑", style=discord.ButtonStyle.red)
  async def cancel_callback(self, button, interaction):
    self.disable_all_items()
    await interaction.response.edit_message(view=self)
    await interaction.followup.send("🛑 Cancelaste la compra de tickets. Deberás entrar de nuevo a la fila si deseas comprar de nuevo.")
    self.cancelled = True
    self.stop()
