import os
from discord.ext import commands
from discord.ext.commands import Bot
import discord
from discord import app_commands, Interaction
from typing import List

class CogManagement(commands.GroupCog, group_name="modules"):
    def __init__(self, bot: Bot):
        super().__init__()  # Ensure the parent class is initialized
        self.bot = bot

    async def cog_autocomplete(self, interaction: Interaction, current: str) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in self.bot.cogs if current.lower() in cog.lower()
        ]

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name='list')
    async def list_cogs(self, interaction: Interaction):
        """Lists all cogs and their status (loaded or unloaded)."""
        embed = discord.Embed(title="Module Status", color=discord.Color.blue())
        cog_directory = 'cogs'  # Directory where cogs are stored
        loaded_cogs = self.bot.extensions.keys()  # Gets the names of all currently loaded cogs

        # Define cogs to exclude from the listing
        excluded_cogs = ['core', 'management_cog']

        # Dynamically list all Python files in the 'cogs' directory as potential cogs, excluding specified ones
        all_cogs = [f"cogs.{filename[:-3]}" for filename in os.listdir(cog_directory)
                    if filename.endswith('.py') and filename[:-3] not in excluded_cogs]

        for cog in all_cogs:
            cog_name = ' '.join(word.capitalize() for word in cog[5:].split('_'))

            # Check if the cog is loaded and mark it as such
            status = 'Loaded' if cog in loaded_cogs else 'Unloaded'
            embed.add_field(name=cog_name, value=status, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name='load')
    @app_commands.autocomplete(cog=cog_autocomplete)
    async def load_cog(self, interaction: Interaction, *, cog: str):
        """Loads a cog."""
        try:
            cog_name = self.bot.cogs[cog].__module__
            await self.bot.load_extension(cog_name)
            await interaction.response.send_message(f'`{cog}` has been loaded!', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'**`ERROR:`** {type(e).__name__} - {e}')

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name='unload')
    @app_commands.autocomplete(cog=cog_autocomplete)
    async def unload_cog(self, interaction: Interaction, *, cog: str):
        """Unloads a cog."""
        try:
            cog_name = self.bot.cogs[cog].__module__
            await self.bot.unload_extension(cog_name)
            await interaction.response.send_message(f'`{cog}` has been unloaded!', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'**`ERROR:`** {type(e).__name__} - {e}')

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name='reload')
    @app_commands.autocomplete(cog=cog_autocomplete)
    async def reload_cog(self, interaction: Interaction, *, cog: str):
        """Reloads a cog."""
        try:
            cog_name = self.bot.cogs[cog].__module__
            await self.bot.reload_extension(cog_name)
            await interaction.response.send_message(f'`{cog}` has been reloaded!', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'**`ERROR:`** {type(e).__name__} - {e}')

async def setup(bot: Bot):
    await bot.add_cog(CogManagement(bot))
