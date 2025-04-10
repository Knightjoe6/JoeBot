import os
import typing

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import check_if_is_admin_or_moderator

# https://mc-mng-api.antdking.io/docs
MC_RCE_API_BASE_URL = "https://mc-mng-api.antdking.io"
MC_RCE_API_KEY = os.environ.get("MC_RCE_API_KEY") or ""
GUILD = discord.Object(id=os.getenv('DISCORD_GUILD'))

ALLOWED_USERS = [
    432916676955078656,  # antdking
]

def is_mc_manager(interaction: discord.Interaction) -> bool:
    return (
        check_if_is_admin_or_moderator(interaction)
        or interaction.user.id in ALLOWED_USERS
    )

class MCManager(commands.GroupCog, group_name="mc"):
    _client: "MCManagerClient"
    def __init__(self, bot: commands.Bot, api_key: str = MC_RCE_API_KEY):
        self.bot = bot
        self._api_key = api_key

    async def cog_load(self):
        self._client = MCManagerClient(self._api_key)

    async def cog_unload(self):
        await self._client.close()

    @app_commands.command(name="status")
    async def get_status(self, interaction: discord.Interaction):
        status = await self._client.get_status()
        embed = discord.Embed(title=f"Minecraft Server Status ({status['latency']}ms)", colour=discord.Colour.teal())
        embed.add_field(name="Server", value="Online" if status["server"] else "Offline", inline=True)
        embed.add_field(name="Tunnel", value="Online" if status["tunnel"] else "Offline", inline=True)
        embed.add_field(name=f"Users ({len(status['users'])})", value="\n".join(status["users"]) or "No users online", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="allow")
    @app_commands.check(is_mc_manager)
    async def allow_user(self, interaction: discord.Interaction, username: str):
        success = await self._client.add_user(username)
        if success:
            await interaction.response.send_message(f"User '{username}' has been allowed.")
        else:
            await interaction.response.send_message(f"User '{username}' could not be added.")

    @app_commands.command(name="remove")
    @app_commands.check(is_mc_manager)
    async def remove_user(self, interaction: discord.Interaction, username: str):
        success = await self._client.remove_user(username)
        if success:
            await interaction.response.send_message(f"User '{username}' has been removed.")
        else:
            await interaction.response.send_message(f"User '{username}' could not be removed.")


class _Status(typing.TypedDict):
    users: list[str]
    server: bool
    tunnel: bool
    latency: int


class MCManagerClient:
    def __init__(self, api_key: str):
        self.session = aiohttp.ClientSession(
            base_url=MC_RCE_API_BASE_URL,
            headers={"x-api-key": api_key},
        )

    async def close(self):
        await self.session.close()

    async def get_status(self) -> _Status:
        async with self.session.get("/healthz/full") as resp:
            resp.raise_for_status()
            payload = await resp.json()
        return _Status(
            users=payload["mc"]["online_users"],
            server=payload["mc"]["internal"]["reachable"],
            tunnel=payload["mc"]["reachable"],
            latency=payload["mc"]["latency"],
        )

    async def add_user(self, username: str) -> bool:
        async with self.session.post("/allow", params={"username": username}) as resp:
            # TODO: server error handling needed for usernames with whitespace (not allowed)
            if not resp.ok:
                return False
            payload = await resp.json()
        return payload["success"]

    async def remove_user(self, username: str) -> bool:
        async with self.session.delete("/remove", params={"username": username}) as resp:
            # TODO: server error handling needed for usernames with whitespace (not allowed)
            if not resp.ok:
                return False
            payload = await resp.json()
        return payload["success"]


async def setup(bot):
    await bot.add_cog(MCManager(bot))