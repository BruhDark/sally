from discord.ext import commands


class Count(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_member_join(self, member):
    ann_channel = member.guild.get_channel(1120872378247954483)
    await ann_channel.edit(name=str(len(member.guild.members)))

  @commands.Cog.listener()
  async def on_member_remove(self, member):
    ann_channel = member.guild.get_channel(1120872378247954483)
    await ann_channel.edit(name=str(len(member.guild.members)))


def setup(bot):
  bot.add_cog(Count(bot))
