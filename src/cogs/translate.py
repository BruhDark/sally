import datetime
import discord
from discord.ext import commands
from discord import slash_command
import googletrans
from resources import aesthetic

LANGS = ["af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "ceb", "co", "cs", "cy", "da", "de", "el", "en", "eo", "es", "et", "eu", "fa", "fi", "fr", "fy", "ga", "gd", "gl", "gu", "ha", "haw", "he", "hi", "hmn", "hr", "ht", "hu", "hy", "id", "ig", "is", "it", "iw", "ja", "jw", "ka", "kk", "km", "kn", "ko", "ku", "ky", "la", "lb", "lo",
         "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "no", "ny", "or", "pa", "pl", "ps", "pt", "ro", "ru", "rw", "sd", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "st", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "ug", "uk", "ur", "uz", "vi", "xh", "yi", "yo", "zh", "zh-CN", "zh-TW", "zu"]


def get_langs(ctx: discord.AutocompleteContext):
    return [lang for lang in LANGS if lang.startswith(ctx.value.lower())]


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.translator = googletrans.Translator()

    @slash_command(description="Translate text to another language", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("language", description="Language to translate to", autocomplete=get_langs)
    @discord.option("text", description="The text you want to translate")
    @discord.option("hide", description="Hide the response", default=False)
    async def translate(self, ctx: discord.ApplicationContext, language: str, text: str, hide: bool):
        if language.lower() not in LANGS:
            languages = ", ".join(LANGS)
            await ctx.respond(embed=discord.Embed(description=f"{aesthetic.Emojis.error} Target language not found. Make sure it is one of these languages: ```{languages}```", color=aesthetic.Colors.error), ephemeral=True)
            return

        await ctx.defer(ephemeral=hide)

        translation = self.translator.translate(text, dest=language)
        translated_text = translation.text
        detected_source_lang = translation.src
        pronounciation = translation.pronunciation

        embed = discord.Embed(timestamp=datetime.datetime.now(datetime.UTC), color=discord.Color.nitro_pink(
        ), description=f"<:sally:1225256761154600971> Processing text from `{detected_source_lang}` (detected) to `{language}`\n\n**Result:** \n`{translated_text}`")

        if pronounciation:
            embed.add_field(
                name="<:help:988166431109681214> Pronunciation", value=pronounciation)

        embed.set_footer(
            text=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed, ephemeral=hide)

    @discord.message_command(name="Translate to English", description="Translate text to English")
    async def translate_english(self, ctx: discord.ApplicationContext, message: discord.Message):
        translation = self.translator.translate(message.content)
        translated_text = translation.text
        detected_source_lang = translation.src
        pronounciation = translation.pronunciation

        embed = discord.Embed(timestamp=datetime.datetime.utcnow(
        ), color=discord.Color.nitro_pink(), description=f"<:sally:1225256761154600971> Processing text from `{detected_source_lang}` (detected) to `en`\n\n**Result:** \n`{translated_text}`")

        if pronounciation:
            embed.add_field(
                name="<:help:988166431109681214> Pronunciation", value=pronounciation)

        embed.set_footer(
            text=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed, ephemeral=True)

    '''
    @discord.message_command(name="Traducir al Español", description="Traduce el mensaje al español")
    async def translate_spanish(self, ctx: discord.ApplicationContext, message: discord.Message):
        translation = self.translator.translate(message.content, dest="es")
        translated_text = translation.text
        detected_source_lang = translation.src
        pronounciation = translation.pronunciation

        embed = discord.Embed(timestamp=datetime.datetime.utcnow(
        ), color=discord.Color.nitro_pink(), description=f"<:sally:1225256761154600971> Procesando texto de `{detected_source_lang}` (detectado) a `es`\n\n**Resultado:** \n`{translated_text}`")

        if pronounciation:
            embed.add_field(
                name="<:help:988166431109681214> Pronunciación", value=pronounciation)

        embed.set_footer(
            text=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.respond(embed=embed, ephemeral=True)
    '''


def setup(bot: commands.Bot):
    bot.add_cog(Translate(bot))
