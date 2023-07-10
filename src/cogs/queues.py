import discord
from discord import SlashCommandGroup
from discord.ext import commands, tasks
from discord import utils

from resources.views import ProcessTicketView
from resources.database import add_queue, get_queue_message

import asyncio

class JoinQueueView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Entrar a la fila", emoji="⏱", custom_id="queuebutton", style=discord.ButtonStyle.blurple)
    async def joinqueue_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.bot.queue is None:
            await interaction.response.send_message("❌ No hay una fila activa", ephemeral=True)
            return
        
        if self.bot.queue_paused or not self.bot.queue_running:
            await interaction.response.send_message("❌ La fila está pausada. No se admiten más entradas.", ephemeral=True)
            return

        await interaction.response.send_message("<a:loadingsally:1128028768838090843> Entrando a la fila...", ephemeral=True)

        if interaction.client.queue.full():
            await interaction.edit_original_response(content="<a:loadingsally:1128028768838090843> La fila está llena! Entrarás cuando un lugar esté disponible. **No cierres este mensaje o presiones de nuevo el botón.**")
        
        interaction.client.queue_number += 1
        number_static = interaction.client.queue_number
        await interaction.client.queue.put([number_static, interaction.user])
        
        await interaction.edit_original_response(content=f"✅ Entraste a la fila! Tu número es: `{number_static}`")

class QueueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.queue: asyncio.Queue = None
        self.queue_paused = False
        self.bot.queue_running = False

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(JoinQueueView(self.bot))

    @tasks.loop()
    async def process_queue(self, process_channel: discord.TextChannel, queue_message: discord.Message):
        queue = self.queue
        embed_q_msg = queue_message.embeds[0]
        field = embed_q_msg.fields[1]

        print(process_channel)

        while True:
            try:
                await process_channel.send("⛏ Obteniendo un nuevo ticket...")
                item = await asyncio.wait_for(queue.get(), 10)

            except asyncio.TimeoutError:
                await process_channel.send("⛔️ Tiempo de espera agotado. Enfriando motores...")
                field.value = "Esperando..."
                await queue_message.edit(embed=embed_q_msg)
                await asyncio.sleep(5)
                continue

            field.value = item[0]
            await queue_message.edit(embed=embed_q_msg)
            embed = discord.Embed(description="🚸 Esperando datos del usuario...", color=discord.Color.blurple())
            message = await process_channel.send(content=f"📮 Ticket Número: {item[0]} | 🪪 Comprador: {item[1].mention}", embed=embed)

            process_view = ProcessTicketView(message)
            user_embed = discord.Embed(title="❗️ Es tu turno!", color=discord.Color.blurple())
            user_embed.description = f":wave: Hola, {item[1].mention}! Es tu turno para comprar tickets! Recuerda tener tus datos a la mano, desde este mensaje tienes **10 minutos** para completar tu compra o tus tickets serán rechazados.\n\n⚠️ **Tus tickets pueden ser rechazados automáticamente** por proveer IDs de Discord inválidas. Si esto ocurre, perderás tu lugar en la fila."
            user_embed.add_field(name="🎫 Tu lugar en la fila era", value=str(item[0]))

            await item[1].send(embed=user_embed, view=process_view)

            if not await process_view.wait() and not process_view.decided:
                await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
                await message.edit(embed=discord.Embed(description="⛔️ Se recibieron datos inválidos. Ticket cancelado.", color=discord.Color.red()))
                continue

            if await process_view.wait() and not process_view.submitted:
                await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
                await message.edit(embed=discord.Embed(description="⛔️ No se recibieron datos. Ticket cancelado.", color=discord.Color.red()))
                continue

            await process_channel.send(f"📦 Ticket número `{item[0]}` procesado correctamente.")

            queue.task_done()

    queue = SlashCommandGroup("fila")
    
    @queue.command(description="Envia el mensaje de la fila a un canal")
    @discord.default_permissions(administrator=True)
    async def mensaje(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "El canal donde el mensaje de la fila será enviado")):

        embed = discord.Embed()
        embed.color = discord.Color.blurple()
        embed.title = "🌠 Boletos"

        embed.description = "👋 Bienvenido a la fila virtual para la venta de tickets de The Eras Tour en Roblox!\
            \n\n❔ **¿Como accedo a la fila virtual?**\n\nPara acceder a la fila virtual debes presionar el botón debajo de este mensaje! Serás añadido a una fila virtual\
            y trendrás que esperar tu turno. La fila puede estar sujeta a limites, si esta se llena, deberás esperar a que un lugar se libere. **Serás automáticamente añadido a la fila**,\
                **NO** cierres el mensaje que verás o presiones el botón de nuevo.\n\n❔ **¿Que datos debo proporcionar?**\n\nDeberás proporcionar tu ID de usuario o IDs de usuarios de Discord que\
                    van contigo, tu ID debe estar incluida. Por ejemplo, si solo eres tú, cuando se te pregunte, solo deberías enviar algo así: `936389482511478804`. En caso de ser más, tu mensaje se debería\
                        ver así: `936389482511478804, 779403860606713906, ...`.\nSi no sabes conseguir tu o las IDs de Discord de las cuentas, héchale un vistazo a: https://support.discord.com/hc/es/articles/206346498\
                            \n\nTambién deberas proporcionar tu usuario, o los usuarios, de Roblox de las personas que van contigo. **Tu usuario también!**"
        
        embed.add_field(name="⚠️ Importante", value=f"**Mantén tus Mensajes Directos (DMs) abiertos!** Cuando sea tu turno, {ctx.guild.me.mention} te enviará un mensaje para comenzat el proceso de venta de los tickets.\
                        Luego tus tickets serán enviados a revisión y se te enviará otro mensaje para notificar si fueron aprobados o denegados.")
        
        embed.add_field(name="🛃 Número de ticket siendo procesado ahora", value="No hay ninguna fila activa!")
        message = await channel.send(embed=embed, view=JoinQueueView(self.bot))
        await add_queue(message.id, message.channel.id)

        await ctx.respond("🪄 Hecho! He enviado el mensaje.")

    @queue.command(description="Crea una fila con un limite. La fila no empieza")
    @discord.default_permissions(administrator=True)
    async def crear(self, ctx, limit: int):

        self.bot.queue = self.queue = asyncio.Queue(limit)
        self.bot.queue_number = 0
        await ctx.respond(f"✅ Creaste una fila con un límite de: {limit}")

    @queue.command(description="Empieza a correr la fila procesando a los usuarios")
    @discord.default_permissions(administrator=True)
    async def empezar(self, ctx, channel: discord.TextChannel):
        if self.queue is None:
            return await ctx.respond("❌ No has creado una fila!")

        await ctx.respond("✅ Hecho! He empezado la fila.")

        queue_msg, channel_id = await get_queue_message()

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        self.bot.queue_running = True
        self.process_queue.start(channel, msg)

    @queue.command(description="Pausa la fila")
    @discord.default_permissions(administrator=True)
    async def pausar(self, ctx):
        if self.bot.queue_paused:
            self.bot.queue_paused = False
            await ctx.respond("✅ Hecho! He despausado la fila.")

        else:
            self.bot.queue_paused = True
            await ctx.respond("✅ Hecho! He pausado la fila. Los usuarios no podrán entrar a la fila, pero los ya añadidos seguirán siendo procesados.")

    @queue.command(description="Cierra la fila y deja de procesar usuarios")
    @discord.default_permissions(administrator=True)
    async def detener(self, ctx):
        await ctx.respond("✅ Hecho! He cerrado la fila. No hay fila activa y ningún usuario será procesado si es que estaban en la fila.")
        self.process_queue.cancel()
        self.bot.queue_number = 0
        self.bot.queue = self.queue = None
        self.bot.queue_running = True

        queue_msg, channel_id = await get_queue_message()

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        embed = msg.embeds[0]
        embed.fields[1].value = "No hay ninguna fila activa!"
        await msg.edit(embed=embed)

def setup(bot):
    bot.add_cog(QueueCommands(bot))