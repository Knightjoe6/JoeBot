from discord.ext import commands
from discord import app_commands, Interaction, ui, ButtonStyle
from discord.ext.commands import Bot

from keys import GameKeyManager
from paginatedview import PaginatedView
from utils.checks import check_if_is_admin_or_moderator


class GameKeysCog(commands.GroupCog, group_name="keys"):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(num_keys='The number of keys to get')
    @app_commands.check(check_if_is_admin_or_moderator)
    async def get(self, interaction: Interaction, num_keys: int):
        """Gets a number of game keys from the database and provides a system for marking them as redeemed"""
        key_manager = GameKeyManager()
        keys = key_manager.get_random_unredeemed_keys(num_keys)

        def create_button_callback(key, btn):
            async def button_click(btn_interaction: Interaction):
                key_manager = GameKeyManager()
                success: bool = key_manager.mark_as_redeemed(key['game_key'])
    
                if not success:
                    msg = "The request failed to update the database. Please try again"
                    await btn_interaction.response.send_message(msg, ephemeral=True)
                    return
                msg: str = f"{key['name']}: {key['game_key']}"
                await btn_interaction.response.send_message(msg, ephemeral=True)
                btn.disabled = True
                btn.label = "Redeemed"
                await interaction.edit_original_response(view=view)
            return button_click

        view = ui.View(timeout=None)
        for i, key in enumerate(keys):
            # await interaction.response.send_message(text_to_send)
            btn: ui.Button = ui.Button(custom_id=f"key{i}", label=f"{key['name']}: Mark Redeemed", style=ButtonStyle.primary, row=i)
            view.add_item(btn)
            btn.callback = create_button_callback(key, btn)

        await interaction.response.send_message("Keys:", view=view, ephemeral=True)

    @app_commands.command()
    @app_commands.check(check_if_is_admin_or_moderator)
    async def add(self, interaction: Interaction, title: str, description: str, key: str):
        """Adds a key to the database"""
        key_manager = GameKeyManager()
        success: bool = key_manager.insert_game_key(name=title, description=description, game_key=key)

        if success:
            await interaction.response.send_message(f"{title} was added successfully", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred. Please try again", ephemeral=True)

    @app_commands.command()
    @app_commands.check(check_if_is_admin_or_moderator)
    async def list(self, interaction: Interaction, hide_redeemed: bool = False):
        """Displays a list of all games we have keys for and their status"""
        key_manager = GameKeyManager()
        keys = key_manager.get_key_list(hide_redeemed)

        # if len(keys) > 0:
        paginated_view = PaginatedView(keys)
        await interaction.response.send_message(embed=paginated_view.get_page_embed(), view=paginated_view)
        # else:
        #     await interaction.response.send_message(f"An error occurred. Please try again", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GameKeysCog(bot))