import discord
from discord.ext import commands
from resources import webhook_manager, aesthetic, errors


class OnCommandError(commands.Cog):
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        base_embed = discord.Embed(color=aesthetic.Colors.error)
        base_embed.description = f"{aesthetic.Emojis.error} "

        if isinstance(error, commands.NotOwner):
            pass

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, errors.RobloxDataFetchFailed):
            base_embed.description += "Failed to fetch Roblox data. If the issue persists, contact the developer."

        else:
            base_embed.description += f"Something went wrong.\n\n```py\n{error}\n```"

            await webhook_manager.send_command_error(ctx, error)
            await ctx.reply(embed=base_embed, mention_author=False)


def setup(bot):
    bot.add_cog(OnCommandError())
