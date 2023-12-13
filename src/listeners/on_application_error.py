import discord
from discord.ext import commands
from resources import webhook_manager


class OnApplicationCommandError(commands.Cog):
    @commands.Cog.listener("on_application_command_error")
    async def on_application_command_error(self, ctx, error):
        base_embed = discord.Embed(color=discord.Color.red())
        base_embed.description = "<:x_:1174507495914471464> "

        if isinstance(error, commands.NoPrivateMessage):
            base_embed.description += "This command is only available in a guild."

        elif isinstance(error, commands.MissingPermissions):
            base_embed.description += f"I am missing the following permissions: `{', '.join(error.missing_permissions)}`"

        elif isinstance(error, commands.CheckFailure):
            base_embed.description += str(error)

        else:
            base_embed.description += f"Something went wrong.\n\n```py\n{error}\n```"
            await webhook_manager.send_command_error(ctx, error)

        await ctx.respond(embed=base_embed)


def setup(bot):
    bot.add_cog(OnApplicationCommandError())
