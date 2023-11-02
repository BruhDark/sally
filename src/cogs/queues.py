import discord
from discord import SlashCommandGroup
from discord.ext import commands, tasks
from discord import utils

from datetime import datetime, timedelta
from resources.views import ProcessTicketView
from resources.database import add_queue, get_queue_message, delete_one

import asyncio

class JoinQueueView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Entrar a la fila", emoji="🎫", custom_id="queuebutton", style=discord.ButtonStyle.blurple)
    async def joinqueue_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.bot.queue is None:
            await interaction.response.send_message(embed=discord.Embed(description="❌ No hay una fila activa", color=discord.Color.red()), ephemeral=True)
            return
        
        if self.bot.queue_paused:
            await interaction.response.send_message(embed=discord.Embed(description="❌ La fila está pausada. No se admiten más entradas.", color=discord.Color.red()), ephemeral=True)
            return

        if interaction.user.id in self.bot.users_in_queue:
          return await interaction.response.send_message(embed=discord.Embed(description="❌ Ya estás en la fila.", color=discord.Color.red()), ephemeral=True)

        await interaction.response.send_message(embed=discord.Embed(description="<a:loadingsally:1128028768838090843> Entrando a la fila...", color=discord.Color.blurple()), ephemeral=True)

        if interaction.client.queue.full():
            await interaction.edit_original_response(embed=discord.Embed(description="<a:loadingsally:1128028768838090843> La fila está llena! Entrarás cuando un lugar esté disponible. **No cierres este mensaje o presiones de nuevo el botón.**", color=discord.Color.blurple()))
        
        interaction.client.queue_number += 1
        number_static = interaction.client.queue_number
        self.bot.users_in_queue.append(interaction.user.id)
        await interaction.client.queue.put([number_static, interaction.user])
        
        try:
          await interaction.edit_original_response(embed=discord.Embed(description=f"✅ Entraste a la fila! Tu número es: `{number_static}`", color=discord.Color.green()))
        except:
          pass
        
        try:
          await interaction.user.send(embed=discord.Embed(description=f"✅ Entraste a la fila! Tu número es: `{number_static}`", color=discord.Color.green()))

        except:
          await interaction.followup.send(embed=discord.Embed(description="❌ Detecté que tus mensajes directos están cerrados. Por favor abrelos o cuando sea tu turno serás automáticamente salteado.", color=discord.Color.red()), ephemeral=True)

class QueueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.queue: asyncio.Queue = None
        self.queue_paused = False
        self.bot.queue_running = False
        self.running_queues = []
        self.processing_numbers = []
        self.bot.users_in_queue = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(JoinQueueView(self.bot))


    async def process_queue(self, process_channel: discord.TextChannel, queue_message: discord.Message, message_index: int):
        queue = self.queue
        embed_q_msg = queue_message.embeds[0]
        field = embed_q_msg.fields[1]

        print(process_channel)

        while True:
            try:
                await process_channel.send("📫 Obteniendo un nuevo ticket...")
                item = await asyncio.wait_for(queue.get(), 10)

            except asyncio.TimeoutError:
                await process_channel.send("⛔️ No pude conseguir un ticket. Esperando un poco.")
                self.processing_numbers[message_index] = "N/A"
                field.value = ", ".join(self.processing_numbers)
                await queue_message.edit(embed=embed_q_msg)
                await asyncio.sleep(10)
                continue

            self.processing_numbers[message_index] = str(item[0])
            field.value = ", ".join(self.processing_numbers)
            await queue_message.edit(embed=embed_q_msg)
            embed = discord.Embed(description="🚸 Esperando datos del usuario...", color=discord.Color.blurple())
            time = utils.format_dt(datetime.utcnow()+timedelta(minutes=3), "R")
            message = await process_channel.send(content=f"📮 Ticket Número: {item[0]} | 🪪 Comprador: {item[1].mention} | ⌛️ Expira {time}", embed=embed)

            process_view = ProcessTicketView(message, process_channel.guild.id)
            user_embed = discord.Embed(title="❗️ Es tu turno!", color=discord.Color.blurple())
            user_embed.description = f":wave: Hola, {item[1].mention}! Es tu turno para comprar tickets! Recuerda tener tus datos a la mano, desde este mensaje tienes **3 minutos** para completar tu compra o tus tickets serán rechazados.\n\n⚠️ **Tus tickets pueden ser rechazados automáticamente** por proveer IDs de Discord inválidas. Si esto ocurre, perderás tu lugar en la fila."
            user_embed.add_field(name="🎫 Tu lugar en la fila era", value=str(item[0]))
            user_embed.add_field(name="⌛️ Tu ticket expirará en", value=utils.format_dt(datetime.utcnow()+timedelta(minutes=3), "R"))
            
            try:
              await item[1].send(embed=user_embed, view=process_view)
            
            except:
              await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
              await message.edit(embed=discord.Embed(description="⛔️ No pude enviar el mensaje.", color=discord.Color.red()))
              self.bot.users_in_queue.remove(item[1].id)
              continue
              
            buy_tickets_view = await process_view.wait()
            if not buy_tickets_view and process_view.cancelled:
              await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
              await message.edit(embed=discord.Embed(description="⛔️ El ticket fue cancelado por el usuario.", color=discord.Color.red()))
              self.bot.users_in_queue.remove(item[1].id)
              continue
            
            if not buy_tickets_view and not process_view.decided:
                await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
                await message.edit(embed=discord.Embed(description="⛔️ Se recibieron datos inválidos. Ticket cancelado.", color=discord.Color.red()))
                self.bot.users_in_queue.remove(item[1].id)
                continue

            if buy_tickets_view and not process_view.submitted:
                await process_channel.send(f"⛔️ Tiempo de espera agotado para: {item[0]}.")
                await message.edit(embed=discord.Embed(description="⛔️ No se recibieron datos. Ticket cancelado.", color=discord.Color.red()))
                self.bot.users_in_queue.remove(item[1].id)
                continue

            

            await process_channel.send(f"📦 Ticket número `{item[0]}` procesado correctamente.")
            self.bot.users_in_queue.remove(item[1].id)

            queue.task_done()

    queue = SlashCommandGroup("fila")
    
    @queue.command(description="Envia el mensaje de la fila a un canal")
    @commands.has_permissions(administrator=True)
    async def mensaje(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "El canal donde el mensaje de la fila será enviado")):

        embed = discord.Embed()
        embed.color = discord.Color.blurple()
        embed.title = "🌠 Renaissance Ent."

        embed.description = "👋 Bienvenido a la fila virtual para la venta de tickets!\n\n❔ **¿Como accedo a la fila virtual?**\n\nPara acceder a la fila virtual debes presionar el botón debajo de este mensaje! Serás añadido a una fila virtual y trendrás que esperar tu turno. La fila puede estar sujeta a limites, si esta se llena, deberás esperar a que un lugar se libere. **Serás automáticamente añadido a la fila**, **NO** cierres el mensaje que verás o presiones el botón de nuevo.\n\n❔ **¿Que datos debo proporcionar?**\n\nDeberás proporcionar tu ID de usuario o IDs de usuarios de Discord que van contigo, **tu ID debe estar incluida**. Por ejemplo, si solo eres tú, cuando se te pregunte, solo deberías enviar algo así: `936389482511478804`. En caso de ser más, tu mensaje se debería ver así: `936389482511478804, 779403860606713906, ...`.\nSi no sabes conseguir tu o las IDs de Discord de las cuentas, héchale un vistazo a: https://support.discord.com/hc/es/articles/206346498\n\nTambién deberas proporcionar tu usuario, o los usuarios, de Roblox de las personas que van contigo. **Tu usuario también!**"
        
        embed.add_field(name="⚠️ Importante", value=f"**Mantén tus Mensajes Directos (DMs) abiertos!** Cuando sea tu turno, {ctx.guild.me.mention} te enviará un mensaje para comenzar el proceso de venta de los tickets. Luego tus tickets serán enviados a revisión y se te enviará otro mensaje para notificar si fueron aprobados o denegados.")
        
        embed.add_field(name="🛃 Número de ticket siendo procesado ahora", value="No hay ninguna fila activa!")
        message = await channel.send(embed=embed, view=JoinQueueView(self.bot))
        if await get_queue_message(ctx.guild.id):
          await delete_one("queues", {"queue_id": ctx.guild.id})
        
        await add_queue(ctx.guild.id, message.id, message.channel.id)

        await ctx.respond(embed=discord.Embed(description="🪄 Hecho! He enviado el mensaje.", color=discord.Color.blurple()))

    @queue.command(description="Crea una fila con un limite. La fila no empieza")
    @discord.default_permissions(administrator=True)
    async def crear(self, ctx, limit: int):

        self.bot.queue = self.queue = asyncio.Queue(limit)
        self.bot.queue_number = 0
        embed = discord.Embed(description=f"✅ Creaste una fila con un límite de: {limit}", color=discord.Color.green())
        await ctx.respond(embed=embed)

        queue_msg, channel_id = await get_queue_message(ctx.guild.id)

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        embed = msg.embeds[0]
        embed.fields[1].value = "Fila activa. Esperando comienzo."
        await msg.edit(embed=embed)

    @queue.command(description="Empieza a correr la fila procesando a los usuarios")
    @discord.default_permissions(administrator=True)
    async def empezar(self, ctx, channel: discord.TextChannel):
        if self.queue is None:
            embed = discord.Embed(description="❌ No has creado una fila!", color=discord.Color.red())
            return await ctx.respond(embed=embed)

        embed = discord.Embed(description=f"✅ Hecho! He creado un procesador de fila en {channel.mention}", color=discord.Color.green())
        await ctx.respond(embed=embed)

        queue_msg, channel_id = await get_queue_message(ctx.guild.id)

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        self.bot.queue_running = True
        message_index = len(self.processing_numbers)
        self.processing_numbers.append("N/A")
        task = asyncio.create_task(self.process_queue(channel, msg, message_index))
        self.running_queues.append(task)
        queue_embed = msg.embeds[0]
        field = queue_embed.fields[1]
        field.value = ", ".join(self.processing_numbers)
        await msg.edit(embed=queue_embed)

    @queue.command(description="Reinicia la fila")
    @discord.default_permissions(administrator=True)
    async def reiniciar(self, ctx, channel: discord.TextChannel):
        if self.queue is None:
              embed = discord.Embed(description="❌ No has creado una fila!", color=discord.Color.red())
              return await ctx.respond(embed=embed)

        embed = discord.Embed(description=f"✅ Hecho! He reiniciado el proceso de la fila.", color=discord.Color.green())
        await ctx.respond(embed=embed)
        for task in self.running_queues:
          task.cancel()
          self.running_queues.remove(task)
          

        queue_msg, channel_id = await get_queue_message(ctx.guild.id)

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        self.bot.queue_running = True
        self.processing_numbers = []
        self.running_queues = []
        task = asyncio.create_task(self.process_queue(channel, msg, 0))
        self.running_queues.append(task)

    @queue.command(description="Pausa la fila")
    @commands.has_permissions(administrator=True)
    async def pausar(self, ctx):
        if self.bot.queue_paused:
          self.bot.queue_paused = False
          await ctx.respond(embed=discord.Embed(description=f"✅ He despausado la fila.", color=discord.Color.green()))

        else:
          self.bot.queue_paused = True
          await ctx.respond(embed=discord.Embed(description=f"✅ He pausado la fila. No se admiten más usuarios, pero la fila se sigue procesando.", color=discord.Color.green()))

    @queue.command(description="Cierra la fila y deja de procesar usuarios")
    @commands.has_permissions(administrator=True)
    async def detener(self, ctx):
        await ctx.respond(embed=discord.Embed(description="✅ Hecho! He cerrado la fila. No hay fila activa y ningún usuario será procesado si es que estaban en la fila.", color=discord.Color.green()))
      
        running_queues = self.running_queues
        for task in running_queues:
          task.cancel()
          self.running_queues.remove(task)

        self.processing_numbers = []
        self.running_queues = []
        self.bot.queue_number = 0
        self.bot.queue = self.queue = None
        self.bot.queue_running = True

        queue_msg, channel_id = await get_queue_message(ctx.guild.id)

        msg = self.bot.get_message(queue_msg)
        if msg is None:
            queue_msg_channel = self.bot.get_channel(channel_id)
            msg = await queue_msg_channel.fetch_message(queue_msg)

        embed = msg.embeds[0]
        embed.fields[1].value = "No hay ninguna fila activa!"
        await msg.edit(embed=embed)

def setup(bot):
    bot.add_cog(QueueCommands(bot))