from typing import Optional
from discord.ext import commands
from discord.ext.commands import Cog, Bot
from discord import app_commands, Interaction, Member, Guild, Embed
from random import randint


SPSP_STICKER_NAME = "spspsps"

class SpSpCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def cooldown_for_everyone_but_admin(interaction: Interaction) -> Optional[app_commands.Cooldown]:
        if interaction.user.get_role(736594738496536676):
            return None
        return app_commands.Cooldown(3, 3600.0)

    @app_commands.command(name="spsp")
    @app_commands.checks.dynamic_cooldown(factory=cooldown_for_everyone_but_admin, key=lambda i: (i.guild_id, i.user.id))
    async def spray_member(self, interaction: Interaction, *, member: Member):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        if not member.avatar:
            await interaction.response.send_message("Member has no avatar.", ephemeral=True)
            return
        # by default, size is set to 1024, so reduce it to 160
        # NOTE: this doesn't reduce the embed size, so just leave it alone :/
        #avatar_url = furl.furl(member.avatar.url).remove("size").add({"size": 160}).url
        if randint(0, 10) < 2 or member == self.bot.user or member.id == 233128300602458113:
            avatar_url = interaction.user.display_avatar.with_size(256).url
        else:
            avatar_url = member.display_avatar.with_size(256).url
        spsp_sticker_url = self._get_spsp_sticker_url(guild)
        if not spsp_sticker_url:
            await interaction.response.send_message("SPSP sticker not found.", ephemeral=True)
            return
        await interaction.response.send_message(embeds=[
            Embed(
                url="https://realcivilengineer.com/",
                #description="SPSPSPS",
            ).set_image(url=spsp_sticker_url),
            Embed(
                url="https://realcivilengineer.com/",
                #description=f"Avatar of {member.display_name}",
            ).set_image(url=avatar_url),
        ])


    def _get_spsp_sticker_url(self, guild: Guild):
        for sticker in guild.stickers:
            if sticker.name == SPSP_STICKER_NAME:
                sticker = sticker
                break
        else:
            return
        # Stickers go to a different url now
        # sticker_url = sticker.url
        sticker_url = f'https://media.discordapp.net/stickers/{sticker.id}.{sticker.format.file_extension}'
        return sticker_url


async def setup(bot: Bot):
    await bot.add_cog(SpSpCog(bot))