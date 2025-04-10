from discord.ext import commands
from discord.ext.commands import Bot
from discord import app_commands, TextChannel, Interaction, Object, NotFound

import os
from utils.checks import check_if_is_admin_or_moderator


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.rename(text_to_send='text', channel='channel')
    @app_commands.describe(text_to_send='Text to send', channel='Channel to send the message to')
    @app_commands.check(check_if_is_admin_or_moderator)
    async def send(self, interaction: Interaction, text_to_send: str, channel: TextChannel = None, message_id: str = None):
        """Sends the text to a specified channel, optionally replying to a message."""

        if channel is None:
            channel = interaction.channel

        if message_id:
            try:
                message = await channel.fetch_message(message_id)
                await message.reply(text_to_send)
            except NotFound:
                await interaction.response.send_message("Message to reply to was not found.", ephemeral=True)
                return
        else:
            await channel.send(text_to_send)

        # Acknowledge the interaction
        await interaction.response.send_message(f"Message sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="sync")
    @app_commands.check(check_if_is_admin_or_moderator)
    async def sync(self, interaction: Interaction):
        GUILD: str = Object(id=os.getenv('DISCORD_GUILD'))
        
        self.bot.tree.copy_global_to(guild=GUILD)
        await self.bot.tree.sync(guild=GUILD)
        await interaction.response.send_message("Sync complete", ephemeral=True)

async def setup(bot: Bot):
    await bot.add_cog(Core(bot))