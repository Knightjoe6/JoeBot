# bot.py
#!/venv/bin/ python
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, UTC
import asyncio

from taskscheduler import TaskScheduler

# Basic logging setup
# Configure logging
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

# Create a rotating file handler
handler = RotatingFileHandler(
    filename='bot_error.log', 
    mode='a', 
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=5,         # Keep 5 backup logs
    encoding='utf-8', 
    delay=0
)

# Set the logging format
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Override default exception hook
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD: str = discord.Object(id=os.getenv('DISCORD_GUILD'))

# Setting up intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guild_typing = True
intents.reactions = True

# Using commands.Bot instead of discord.Client
bot = commands.Bot(command_prefix="!", intents=intents)  # Choose an appropriate prefix

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    bot.task_scheduler = TaskScheduler()

    activity = discord.Activity(type=discord.ActivityType.watching, name="the humans")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def setup_hook() -> None:
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded {filename}")

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command) -> None:
    guild: discord.guild = interaction.guild
    log_channel: discord.TextChannel = guild.get_channel(1252425409845264414)

    command_string = f"\\{command.name} " + ' '.join(f"{option['name']}:{option['value']}" for option in interaction.data['options'])

    if command.name == 'weather':
        return

    if log_channel:
        embed = discord.Embed(
            description=f"Used **`{command.name}`** command in {interaction.channel.mention}\n`{command_string}`",
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        embed.set_footer(text=f"User ID: {interaction.user.id} | Command: {command.name}")

        await log_channel.send(embed=embed)

async def run_bot():
    while True:
        try:
            async with bot:
                await bot.start(TOKEN)
        except (discord.DiscordException, asyncio.TimeoutError) as e:
            logging.error(f'Bot disconnected due to {e.__class__.__name__}. Attempting to reconnect...')
            await asyncio.sleep(30)  # Wait 30 seconds before attempting to reconnect
        except Exception as e:
            logging.error("Unhandled exception", exc_info=True)
            break

if __name__ == "__main__":
    asyncio.run(run_bot())
