import discord
from discord import slash_command
from discord.ext import commands
from resources.database import add_date, get_date


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    dates = discord.SlashCommandGroup("fechas")

    @dates.command(description="Añade una nueva fecha con sus datos")
    @discord.default_permissions(administrator=True)
    async def añadir(self, ctx: discord.ApplicationContext, id: discord.Option(str, "El ID de la fecha. Ej: TS1"), fecha: discord.Option(str, "La fecha a añadir. Ej: 10/07/23"), tickets: discord.Option(int, "La cantidad de tickets que se venderán"), rol: discord.Option(discord.Role, "El rol que será asignado a las personas que compren un ticket para esta fecha")):
        id: str = id.upper()
        date = await get_date(id)
        if date:
            return await ctx.respond(content="❌ Ups! Una fecha con esa ID ya existe!")

        await add_date(id, fecha, tickets, rol.id)
        await ctx.respond("🪄 Hecho! Has añadido una fecha.")

    @dates.command(description="Visualiza una fecha por su ID")
    @discord.default_permissions(administrator=True)
    async def visualizar(self, ctx: discord.ApplicationContext, id: discord.Option(str, "El ID de la fecha. Ej: TS1")):

        date = await get_date(id)
        if not date:
            return await ctx.respond("❌ No pude encontrar esa fecha.")

        embed = discord.Embed(color=discord.Color.blurple(), title="Información de fecha añadida")
        embed.add_field(name="📅 Fecha", value=date["date"])
        embed.add_field(name="🎫 Cantidad de Tickets", value=str(date["tickets_amount"]))
        embed.add_field(name="💸 Cantidad de Tickets vendidos", value=str(date["tickets_sold"]))
        embed.add_field(name="🧮 Cantidad de Tickets disponibles", value=str(date["tickets_available"]))

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(AdminCommands(bot))