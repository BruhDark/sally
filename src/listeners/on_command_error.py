import discord
from discord.ext import commands
from resources import webhook_manager


class OnCommandError(commands.Cog):
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        base_embed = discord.Embed(color=discord.Color.red())
        base_embed.description = "<:x_:1174507495914471464> "

        if isinstance(error, commands.NotOwner):
            pass

        elif isinstance(error, commands.CommandNotFound):
            pass

        else:
            base_embed.description += f"Something went wrong.\n\n```py\n{error}\n```"

            await webhook_manager.send_command_error(ctx, error)
            await ctx.reply(embed=base_embed, mention_author=False)


def setup(bot):
    bot.add_cog(OnCommandError())
