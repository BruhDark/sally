import discord
from discord.ext import commands, tasks
import os
from aiohttp import web
from resources.database import get_roblox_info_by_rbxid
from resources import webhook_manager
import datetime
import dotenv

dotenv.load_dotenv()

# app = Flask(__name__)
app = web.Application()
routes = web.RouteTableDef()


class App(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.web_server.start()
        app.bot = bot

        app.add_routes(routes)

    @tasks.loop(count=1)
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        port = os.getenv("PORT")
        if port == None:
            print("No port found. Did not start web server.")
            return
        site = web.TCPSite(
            runner, port=int(port))
        await site.start()
        print("[API Server] Started!")

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()

    @routes.get("/")
    async def index(request: web.Request):
        resp = {'success': True, 'message': "Server is live"}
        return web.json_response(resp)

    # ROBLOX ENDPOINTS

    @routes.get("/roblox/is-blacklisted")
    async def is_blacklisted(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'blacklisted': True, 'message': 'Improper request made'}, status=404)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)

        if not roblox_data:
            message = "User is not verified with Sally"
            resp = {'discord_id': None,
                    'blacklisted': True, 'message': message}

        elif roblox_data["blacklisted"]:
            message = roblox_data["message"]
            resp = {'discord_id': roblox_data["user_id"],
                    'blacklisted': True, 'message': message}

        else:
            resp = {'discord_id': roblox_data["user_id"],
                    'blacklisted': False, 'message': "User is not blacklisted"}

        return web.json_response(resp)

    @routes.get("/roblox/is-booster")
    async def is_booster(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'booster': False, 'message': 'Improper request made'}, status=404)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        if roblox_data == None:
            resp = {"booster": False}

        else:
            inkigayo: discord.Guild = app.bot.get_guild(1170821546038800464)
            server_booster = inkigayo.get_role(1177467255802564698)
            vip_role = discord.utils.get(inkigayo.roles, name="VIPS")
            member = inkigayo.get_member(int(roblox_data["user_id"]))

            if not inkigayo or not member:
                resp = {"booster": False}

            elif server_booster in member.roles or vip_role in member.roles:
                resp = {"booster": True}

            else:
                resp = {"booster": False}

        return web.json_response(resp)

    @routes.get("/roblox/get-info")
    async def get_info(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'success': False, 'message': 'Improper request made'}, status=404)
        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        roblox_data["_id"] = "."
        if not roblox_data:
            return web.json_response({'success': False, 'message': 'User is not verified with Sally'}, status=404)
        return web.json_response(roblox_data)

    @routes.post("/roblox/join")
    async def roblox_join(request: web.Request):
        roblox_id = await request.json()
        roblox_id = roblox_id["roblox_id"]

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())

        if roblox_data:
            embed.add_field(name="Discord Account",
                            value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
            embed.add_field(name="Roblox Account",
                            value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
            embed.set_thumbnail(url=roblox_data["data"]["avatar"])

        else:
            embed.add_field(name="Discord Account",
                            value=f"Unknown")
            embed.add_field(name="Roblox Account",
                            value=str(roblox_id))

        await webhook_manager.send_join_log(embed)
        return web.json_response({"success": True}, status=201)

    @routes.get("/roblox/test-join")
    async def roblox_join(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id")

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())
        embed.add_field(name="Discord Account",
                        value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
        embed.add_field(name="Roblox Account",
                        value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
        embed.set_thumbnail(url=roblox_data["data"]["avatar"])

        logs = app.bot.get_channel(1183581233821790279)  # 1183581233821790279
        await logs.send(embed=embed)
        return web.json_response({"success": True})

    # ROBLOX VERIFICATION ENDPOINTS

    @routes.get("/verification/check")
    async def check_verication(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id")
        if roblox_id == None:
            return web.json_response({"success": False, "message": "Improper request made"})

        discord_member = app.bot.pending_verifications.get(roblox_id)
        if discord_member == None:
            return web.json_response({"success": False, "message": "Could not find pending verication"})

        response = {"success": True,
                    "username": discord_member["username"], "id": discord_member["id"]}
        return web.json_response(response)

    @routes.post("/verification/complete")
    async def complete_verification(request: web.Request):
        data = await request.json()
        roblox_id = int(data["roblox_id"])
        discord_id = int(data["discord_id"])
        if roblox_id is None or discord_id is None:
            return web.json_response({"success": False, "message": "Improper request made"})

        try:
            app.bot.dispatch("verification_completed", roblox_id, discord_id)
            app.bot.pending_verifications.pop(str(roblox_id))
            return web.json_response({"success": True}, status=201)
        except Exception as e:
            print(e)
            return web.json_response({"success": False, "message": "An error occured"}, status=409)

    # ROBLOX LOCK ENDPOINTS

    @routes.get("/lock/check-user")
    async def check_user(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id")
        if roblox_id == None:
            return web.json_response({"success": False, "message": "Improper request made"})

        user = await get_roblox_info_by_rbxid(roblox_id)
        if user == None:
            return web.json_response({"success": False, "message": "User not found"}, status=404)

        inkigayo = app.bot.get_guild(1170821546038800464)
        member = inkigayo.get_member(int(user["user_id"]))
        if member == None:
            return web.json_response({"success": False, "message": "User not found"})

        staff_role = inkigayo.get_role(1224881097146372226)
        artists_role = inkigayo.get_role(1224881164569808927)
        vip_role = inkigayo.get_role(1179032931457581107)

        data = {"success": True, "staff": False, "artist": False, "vip": False}

        if staff_role in member.roles:
            data["staff"] = True
        if artists_role in member.roles:
            data["artist"] = True
        if vip_role in member.roles:
            data["vip"] = True

        return web.json_response(data)


def setup(bot):
    bot.add_cog(App(bot))
