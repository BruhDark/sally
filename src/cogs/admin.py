import discord
from discord import slash_command
from discord.ext import commands, pages
from resources.database import add_date, get_date, delete_one, return_dates, delete_date, return_all


class AdminCommands(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    dates = discord.SlashCommandGroup(
        "fechas", guild_ids=[1120863134878547969, 881968885279117342])

    @commands.is_owner()
    @commands.command(name="deleteinvalid")
    async def delete_invalid_dates(self, ctx):
        dates = await return_dates(ctx.guild.id)
        await ctx.send("Procesando...")
        for date in dates:
            if date["tickets_available"] == 0:
                await delete_date(date["date_id"])

        await ctx.send("Hecho. Borré aquellas fechas cuya disponibilidad era de 0."
                       )

    @dates.command(description="Elimina una fecha")
    @commands.has_permissions(administrator=True)
    async def eliminar(self, ctx, id: str):
        if not await get_date(id.upper()):
            return await ctx.respond(embed=discord.Embed(
                description="❌ Ups! Una fecha con esa ID no existe!",
                color=discord.Color.red()))

        await delete_one("dates", {"date_id": id.upper()})
        await ctx.respond(embed=discord.Embed(
            description=f"🪄 Hecho! Has eliminado la fecha: `{id}`",
            color=discord.Color.blurple()))

    @dates.command(description="Añade una nueva fecha con sus datos")
    @commands.has_permissions(administrator=True)
    async def añadir(
            self, ctx: discord.ApplicationContext,
            id: discord.Option(str, "El ID de la fecha. Ej: TS1"),
            fecha: discord.Option(str, "La fecha a añadir. Ej: 10/07/23"),
            tickets: discord.Option(int, "La cantidad de tickets que se venderán"),
            rol: discord.Option(
                discord.Role,
                "El rol que será asignado a las personas que compren un ticket para esta fecha"
            )):
        id: str = id.upper()
        date = await get_date(id)
        if date:
            return await ctx.respond(embed=discord.Embed(
                description="❌ Ups! Una fecha con esa ID ya existe!",
                color=discord.Color.red()))

        await add_date(ctx.guild.id, id, fecha, tickets, rol.id)
        await ctx.respond(
            embed=discord.Embed(description="🪄 Hecho! Has añadido una fecha.",
                                color=discord.Color.blurple()))

    @dates.command(description="Visualiza una fecha por su ID")
    @commands.has_permissions(administrator=True)
    async def visualizar(self, ctx: discord.ApplicationContext,
                         date_id: discord.Option(str, "El ID de la fecha. Ej: TS1", default=None)):

        if date_id is None:
            dates = await return_all("dates")
            if len(dates) == 0:
                return await ctx.respond("❌ No hay fechas a visualizar.")
            embeds = []

            for date in dates:
                embed = discord.Embed(color=discord.Color.blurple(),
                                      title=f"Información de fecha: `{date['date_id']}`")

                embed.add_field(
                    name="📅 Fecha", value=date["date"], inline=True)

                embed.add_field(name="🎫 Cantidad de Tickets",
                                value=str(date["tickets_amount"]))

                embed.add_field(name="💸 Cantidad de Tickets vendidos",
                                value=str(date["tickets_sold"]))

                embed.add_field(name="🧮 Cantidad de Tickets disponibles",
                                value=str(date["tickets_available"]))

                embed.add_field(name="Rol a añadir",
                                value=f"<@&{date['role']}>")

                embeds.append(embed)

            paginator = pages.Paginator(
                embeds, show_disabled=False, author_check=True, disable_on_timeout=True)
            await paginator.respond(ctx.interaction)

        else:
            date_id = str(date_id).upper()
            date = await get_date(date_id)
            if not date:
                return await ctx.respond(
                    embed=discord.Embed(description="❌ No pude encontrar esa fecha.",
                                        color=discord.Color.red()))

            embed = discord.Embed(color=discord.Color.blurple(),
                                  title=f"Información de fecha: `{date['date_id']}`")

            embed.add_field(name="📅 Fecha", value=date["date"], inline=True)

            embed.add_field(name="🎫 Cantidad de Tickets",
                            value=str(date["tickets_amount"]))

            embed.add_field(name="💸 Cantidad de Tickets vendidos",
                            value=str(date["tickets_sold"]))

            embed.add_field(name="🧮 Cantidad de Tickets disponibles",
                            value=str(date["tickets_available"]))

            embed.add_field(name="Rol a añadir", value=f"<@&{date['role']}>")

            await ctx.respond(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def say(self, ctx: discord.ApplicationContext, *, text: str):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            return

        message = ctx.message.reference.message_id if ctx.message.reference is not None else None
        message = self.bot.get_message(
            message) if message is not None else None

        await message.reply(text) if message is not None else await ctx.send(text)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
