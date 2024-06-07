import discord
import aiohttp
import datetime
from resources import aesthetic

ROBLOX_USERS_ENDPOINT = "https://users.roblox.com/v1/users/"
ROBLOX_USERNAMES_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

VERIFIED_ROLE_ID = 1245844059373961248
VIP_ROLE_ID = 1241530191725989928


class Embeds:
    @staticmethod
    async def profile_embed(roblox_data: dict, managed: bool = False) -> discord.Embed:
        username = roblox_data["data"]["name"]
        avatar_url = roblox_data["data"]["avatar"]
        display_name = roblox_data["data"]["displayName"]
        roblox_id = roblox_data["roblox_id"]
        created = roblox_data["data"]["created"]
        created = discord.utils.format_dt(
            datetime.datetime.fromisoformat(created), "R")

        embed = discord.Embed(
            title=f":wave: Hello there, {username}!", color=aesthetic.Colors.main)
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="Discord Account",
                        value=f"<@{roblox_data['user_id']}> (`{roblox_data['user_id']}`)")
        embed.add_field(name="Username & Display Name",
                        value=f"{username} (@{display_name})")
        embed.add_field(name="Roblox ID", value=roblox_id)
        embed.add_field(name="Created", value=created)

        if roblox_data["blacklisted"]:
            embed.add_field(name="Blacklist Info",
                            value=str(roblox_data["message"]))

        if managed:
            embed.description = "Description:\n" + \
                roblox_data["data"]["description"]
            embed.title = f"<:info:881973831974154250> Roblox Information for {username}"
        else:
            embed.description = "You are verified! You are able to attend events hosted by **WePeak**.\n\n<:info:881973831974154250> If you wish to **link another account**, first delete your linked account using the `Delete Account` button below and run this command again.\nIf your **Roblox information** is **outdated**, click the `Refresh Data` button.\n\n<:thunderbolt:987447657104560229> Looking to **claim your WePeak Pass role**? Click the `WePeak Pass` button below."

        return embed


async def attempt_avatar_refresh(roblox_data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.get(roblox_data["data"]["avatar"]) as resp:
            if resp.status == 200:
                return

    return await fetch_roblox_data(roblox_data["roblox_id"])


async def fetch_roblox_data(roblox_id: str) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={roblox_id}&size=420x420&format=Png&isCircular=false") as resp:
            if resp.status != 200:
                return

            response = await resp.json()
            avatar_url = response["data"][0]["imageUrl"]

    url = ROBLOX_USERS_ENDPOINT + str(roblox_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 404:
                return
            roblox_data = await response.json()
            roblox_data["avatar"] = avatar_url

    return roblox_data


async def fetch_roblox_description(roblox_id: str) -> str | None:
    url = ROBLOX_USERS_ENDPOINT + str(roblox_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 404:
                return
            roblox_data = await response.json()

    return roblox_data["description"]


async def update_discord_profile(guild: discord.Guild, user_id: int, roblox_data: dict) -> list[str] | None:
    errors = []
    member = guild.get_member(user_id)
    try:
        nickname = roblox_data["name"] if len(
            nickname) > 32 or roblox_data["displayName"] == roblox_data["name"] else f"{roblox_data['displayName']} (@{roblox_data['name']})"
        await member.edit(nick=nickname)
    except:
        errors.append("edit your nickname")

    try:
        await member.add_roles(discord.Object(id=VERIFIED_ROLE_ID), reason=f"Verified account as: {nickname}")
    except:
        errors.append("assign your roles")

    return errors
