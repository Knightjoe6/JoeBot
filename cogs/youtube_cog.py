from discord.ext import commands
from discord import app_commands, Interaction

import youtube


class YouTubeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def sub_count(self, interaction: Interaction):
        """Replies with RCE's 'current' subcount rounded to the nearest 10k"""
        sub_count = youtube.get_sub_count()

        if sub_count >= 1_000_000:
            sub_count = f'{sub_count/1_000_000} million'

        await interaction.response.send_message(f'Real Civil Engineer currently has {sub_count} subscribers')

async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
