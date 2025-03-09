import discord
from discord.ext import commands, tasks
import os
from aiohttp import web
from resources.database import get_roblox_info_by_rbxid
from resources import webhook_manager, verification, aesthetic, database
import datetime
import dotenv

dotenv.load_dotenv()

app = web.Application()
routes = web.RouteTableDef()


def missing_auth(request: web.Request) -> bool:
    auth_code = os.getenv("API_AUTHORIZATION_CODE")
    auth_override = os.getenv("API_AUTHORIZATION_CODE_OVERRIDE")
    if not auth_code or not auth_override:
        raise ValueError(
            "Authorization codes are not set in environment variables.")
    return request.headers.get("Authorization") != auth_code and request.rel_url.query.get("auth") != auth_override


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
        host = os.getenv("HOST", "0.0.0.0")
        if not port:
            print("No port found. Did not start web server.")
            return

        try:
            site = web.TCPSite(runner, host=str(host), port=int(port))
            await site.start()
            print("[API Server] Started!")
        except Exception as e:
            print(e)
            print("Failed to start web server.")
            raise e

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()

    @routes.get("/")
    async def index(request: web.Request) -> web.Response:
        resp = {'success': True, 'message': "Server is live"}
        return web.json_response(resp)

    @routes.get("/privacy")
    async def privacy(request: web.Request) -> web.Response:
        raise web.HTTPFound(
            "https://github.com/BruhDark/sally-tickets/blob/main/privacy-policy.md")

    @routes.get("/terms")
    async def terms(request: web.Request) -> web.Response:
        raise web.HTTPFound(
            "https://github.com/BruhDark/sally-tickets/blob/main/terms.md")

    # ROBLOX ENDPOINTS

    @routes.get("/roblox/get-info")
    async def get_info(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        roblox_id = request.rel_url.query.get("roblox_id")
        if not roblox_id:
            return web.json_response({'success': False, 'message': 'Improper request made'}, status=400)
        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        if not roblox_data:
            return web.json_response({'success': False, 'message': 'User is not verified with Sally'}, status=404)
        roblox_data["_id"] = "."
        return web.json_response(roblox_data)

    @routes.post("/roblox/join")
    async def roblox_join(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        data = await request.json()
        roblox_id = data.get("roblox_id")
        if not roblox_id:
            return web.json_response({"success": False, "message": "Improper request made"}, status=400)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=aesthetic.Colors.main, title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())

        if roblox_data:
            embed.add_field(
                name="Discord Account", value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
            embed.add_field(
                name="Roblox Account", value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
            try:
                embed.set_thumbnail(url=roblox_data["data"]["avatar_url"])
            except KeyError:
                pass
        else:
            embed.add_field(name="Discord Account", value="Unknown")
            embed.add_field(name="Roblox Account", value=str(roblox_id))

        await webhook_manager.send_join_log(embed)
        return web.json_response({"success": True}, status=201)

    # ROBLOX VERIFICATION ENDPOINTS

    @routes.get("/verification/check")
    async def check_verification(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        roblox_id = request.rel_url.query.get("roblox_id")
        if not roblox_id:
            return web.json_response({"success": False, "message": "Improper request made"}, status=400)

        discord_member = app.bot.pending_verifications.get(roblox_id)
        if not discord_member:
            return web.json_response({"success": False, "message": "Could not find pending verification"}, status=404)

        response = {"success": True,
                    "username": discord_member["username"], "id": discord_member["id"]}
        return web.json_response(response)

    @routes.post("/verification/complete")
    async def complete_verification(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        data = await request.json()
        roblox_id = data.get("roblox_id")
        discord_id = data.get("discord_id")
        if not roblox_id or not discord_id:
            return web.json_response({"success": False, "message": "Improper request made"}, status=400)

        try:
            app.bot.dispatch("verification_completed", roblox_id, discord_id)
            app.bot.pending_verifications.pop(str(roblox_id))
            return web.json_response({"success": True}, status=201)
        except Exception as e:
            print(e)
            return web.json_response({"success": False, "message": "An error occurred"}, status=409)

    # ROBLOX LOCK ENDPOINTS

    @routes.get("/lock/check-user")
    async def check_user(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        roblox_id = request.rel_url.query.get("roblox_id")
        if not roblox_id:
            return web.json_response({"success": False, "message": "Improper request made"}, status=400)

        data = {"success": True, "discord_id": None, "blacklisted": True,
                "message": "User is not verified with Sally", "staff": False, "artist": False, "vip": False}
        roblox_data = await get_roblox_info_by_rbxid(roblox_id)

        if not roblox_data:
            return web.json_response(data)

        if roblox_data["blacklisted"]:
            data["message"] = roblox_data["message"]
            return web.json_response(data)

        wepeak = app.bot.get_guild(1240592168754745414)
        member: discord.Member = wepeak.get_member(int(roblox_data["user_id"]))

        if not member:
            return web.json_response({"success": False, "message": "User not found"}, status=404)

        staff_role = wepeak.get_role(1248770684612640910)
        artists_role = wepeak.get_role(1243320082957074473)
        vip_role = wepeak.get_role(verification.VIP_ROLE_ID)

        if staff_role in member.roles:
            data["staff"] = True
        if artists_role in member.roles:
            data["artist"] = True
        if vip_role in member.roles:
            data["vip"] = True

        data["discord_id"] = roblox_data["user_id"]
        data["blacklisted"] = False
        data["message"] = None

        return web.json_response(data)

    # POLLS ENDPOINTS

    @routes.get("/polls/active")
    async def active_polls(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        active_poll = await database.get_active_poll()
        if not active_poll:
            return web.json_response({"success": False, "message": "No active polls found"}, status=404)

        parsed_response = {
            "poll_id": active_poll["_id"], "groups": active_poll["choices"], "status": active_poll["status"]}
        return web.json_response(parsed_response)

    @routes.post("/polls/vote")
    async def vote_poll(request: web.Request) -> web.Response:
        if missing_auth(request):
            return web.json_response({"success": False, "message": "Unauthorized"}, status=401)

        data = await request.json()
        poll_id = data.get("poll_id")
        choice = data.get("choice")
        discord_id = data.get("discord_id")

        if not poll_id or not choice or not discord_id:
            return web.json_response({"success": False, "message": "Improper request made"}, status=400)

        if await database.add_vote(poll_id, discord_id, choice):
            return web.json_response({"success": True}, status=201)


def setup(bot: commands.Bot):
    bot.add_cog(App(bot))
