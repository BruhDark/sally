import discord
from discord.ext import commands, tasks
import os
from aiohttp import web
from resources.database import get_roblox_info_by_rbxid
import datetime
import dotenv

dotenv.load_dotenv()

# app = Flask(__name__)
app = web.Application()
routes = web.RouteTableDef()
api_key = os.getenv("ROBLOX_API_KEY")


class App(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.web_server.start()
        app.bot: commands.Bot = bot

        app.add_routes(routes)

    @routes.get("/")
    async def index(request: web.Request):
        resp = {'success': True, 'message': "Hello world"}
        return web.json_response(resp)

    @routes.get("/roblox/is-blacklisted")
    async def is_blacklisted(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'blacklisted': True, 'message': 'Improper request made'}, status=404)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        if roblox_data == None:
            message = "User is not verified with Sally"
            resp = {'blacklisted': True, 'message': message}
            return web.json_response(resp)

        if roblox_data["blacklisted"]:
            message = roblox_data["message"]
            resp = {'blacklisted': True, 'message': message}
            return web.json_response(resp)

        resp = {'blacklisted': False, 'message': "User is not blacklisted"}
        return web.json_response(resp)

    @routes.get("/roblox/get-info")
    async def get_info(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'blacklisted': True, 'message': 'Improper request made'}, status=404)
        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        return web.json_response(roblox_data)

    @routes.post("/roblox/join")
    async def roblox_join(request: web.Request):
        roblox_id = request.json()
        roblox_id = roblox_id["roblox_id"]

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())
        embed.add_field(name="Discord Account",
                        value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
        embed.add_field(name="Roblox Account",
                        value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
        embed.set_thumbnail(url=roblox_data["data"]["avatar"])

        logs = app.bot.get_channel(1183581233821790279)
        await logs.send(embed=embed)
        return web.json_response({"success": True})

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

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner, host="sally-tickets-82ca1ba8fdc3.herokuapp.com", port=os.getenv("PORT"))
        await site.start()
        print("Started")

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(App(bot))
