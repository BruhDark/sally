import discord
from discord.ext import commands


class OnMemberJoin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != 1170821546038800464:
            return

        embed = discord.Embed(
            title=":wave: Welcome to INKIGAYO! | Season 4 is here!",
            color=discord.Color.nitro_pink()
        )
        embed.set_author(
            name=f"Hey there, {member.display_name}!", icon_url=member.display_avatar.url)
        embed.description = "We are glad you joined the most popular program on KUV! Here at **INKIGAYO** you can discover amazing perfomances by popular groups and soloists, all in our own Roblox game every two weeks.\n\nAs a way to make your stay more enjoyable, consider doing some extra steps:\n<:rightarrow:1173350998388002888> Please take a moment to read our <#1170827515095437363> channel. Keeping our community safe is very important!\n<:rightarrow:1173350998388002888> If you want to join our shows in Roblox, you **must be verified**. You can do it in <#1183809997918965760> or by running `/verify` in a channel.\n<:rightarrow:1173350998388002888> You can learn about VIP benefits in <#1179028774545784943>, you can also earn VIP with our <#1210333568400891925>.\n\n<:help:988166431109681214> **Have any questions?** Check out our <#1214030089382010941> post or create a post in our <#1199750748473397258> forum channel."
        embed.set_footer(text="We hope you enjoy your stay! • INKIGAYO Roblox",
                         icon_url=member.guild.icon.url)

        embed.set_thumbnail(url=member.guild.icon.url)
        f = discord.File("src\resources\images\S4-BANNER.jpg",
                         filename="S4-BANNER.jpg")
        embed.set_image(url="attachment://S4-BANNER.jpg")
        embed.timestamp = discord.utils.utcnow()

        try:
            await member.send(embed=embed)
        except:
            pass


def setup(bot):
    bot.add_cog(OnMemberJoin(bot))
