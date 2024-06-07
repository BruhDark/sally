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


def missing_auth(request: web.Request):
    if request.headers.get("Authorization") == os.getenv("API_AUTHORIZATION_CODE") or request.rel_url.query.get("auth") == os.getenv("API_AUTHORIZATION_CODE_OVERRIDE"):
        return False
    return True


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

    @routes.get("/roblox/get-info")
    async def get_info(request: web.Request):
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

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
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        roblox_id = await request.json()
        roblox_id = roblox_id["roblox_id"]

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=aesthetic.Colors.main, title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())

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

    # ROBLOX VERIFICATION ENDPOINTS

    @routes.get("/verification/check")
    async def check_verication(request: web.Request):
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

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
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

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
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        roblox_id = request.rel_url.query.get("roblox_id")
        if roblox_id == None:
            return web.json_response({"success": False, "message": "Improper request made"})

        # Base response is assuming the user is not verified with Sally and "blacklisted"
        data = {"success": True, "discord_id": None, "blacklisted": True,
                "message": "User is not verified with Sally", "staff": False, "artist": False, "vip": False}

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)

        if not roblox_data:
            # User is not verified with Sally, base response
            return web.json_response(data)

        elif roblox_data["blacklisted"]:
            message = roblox_data["message"]
            data["message"] = message
            # User is blacklisted, just edit the message sent
            return web.json_response(data)

        wepeak = app.bot.get_guild(1240592168754745414)
        member: discord.Member = wepeak.get_member(
            int(roblox_data["user_id"]))

        if not member:
            # Could not resolve a member object
            return web.json_response({"success": False, "message": "User not found"})

        staff_role = wepeak.get_role(1243320002002550804)
        artists_role = wepeak.get_role(1224881164569808927)
        vip_role = wepeak.get_role(1241530191725989928)

        if staff_role in member.roles:
            data["staff"] = True
        if artists_role in member.roles:
            data["artist"] = True
        if vip_role in member.roles:
            data["vip"] = True

        data["discord_id"] = roblox_data["user_id"]
        data["blacklisted"] = False
        data["message"] = None

        return web.json_response(data)  # User is verified and not blacklisted


def setup(bot):
    bot.add_cog(App(bot))
