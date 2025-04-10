from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands.cog import Cog
from discord import Message, utils, TextChannel, Guild, RawReactionActionEvent, NotFound

import re
from datetime import timedelta
from urllib.parse import unquote

import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

BLOCKED_REACTIONS_CHANNELS = {1181067100173910096, 1181066229570605159}
BLOCKED_REACTIONS_EMOJIS = {
    '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', '🇺', '🇻', '🇼', '🇽', '🇾', '🇿',
    '🅰️', '🅱️', '🆎', '🔤', '🔡', '🔠', 'Ⓜ️', 'ℹ️', '🅾️', '🅿️',
}

class SecurityCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.url_pattern = re.compile(r"(https?://)?(www.)?(discord.(gg|io|me|li)|(discordapp.com/invite)|(discord.com/invite))/[^\s/]+?(?=[^\w-]|$)")

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return
        
        allowed_roles = ['Admin', 'Mods']
        user_roles = [role.name for role in message.author.roles]
        if any(role in user_roles for role in allowed_roles):
            return
        
        decoded_content = unquote(message.content)
        invite_link = self.url_pattern.search(decoded_content)

        if invite_link:
            link = invite_link.group()
            author = message.author
            channel = message.channel

            await message.delete()

            guild: Guild = message.guild

            alert_channel: TextChannel = guild.get_channel(1188600358092689518)
            await alert_channel.send(f"message deleted in {channel} from {author} because it contained {link}")

            await author.timeout(utils.utcnow() + timedelta(days=28))

    @Cog.listener("on_raw_reaction_add")
    async def block_emoji_letters(self, payload: RawReactionActionEvent):
        if payload.channel_id not in BLOCKED_REACTIONS_CHANNELS:
            return
        if str(payload.emoji) in BLOCKED_REACTIONS_EMOJIS:
            channel_id = payload.channel_id
            channel = self.bot.get_partial_messageable(channel_id)
            message = channel.get_partial_message(payload.message_id)
            try:
                await message.clear_reaction(payload.emoji)
            except NotFound:
                pass

async def setup(bot):
    await bot.add_cog(SecurityCog(bot))
