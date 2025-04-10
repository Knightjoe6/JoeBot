# bot.py
#!/venv/bin/ python
import os
import sys
import re
import logging
from logging.handlers import RotatingFileHandler
import random
from datetime import datetime, timedelta
import discord
from discord import app_commands, ui, File
from dotenv import load_dotenv
from keys import GameKeyManager
import youtube
from enum import Enum
from pint import UnitRegistry

from paginatedview import PaginatedView

from taskscheduler import TaskScheduler

from editgif import add_text_to_gif

from db import DatabaseConnection

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
TOKEN: str = os.getenv('DISCORD_TOKEN')
GUILD: str = discord.Object(id=os.getenv('DISCORD_GUILD'))


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)
        random.seed()

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        self.task_scheduler: TaskScheduler = TaskScheduler()

    # def run(self, *args, **kwargs):
    #     print("This is the overwritten run method")
    #     super().run(*args, **kwargs)

intents: discord.Intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guild_typing = True

client: MyClient = MyClient(intents=intents)

# task_scheduler: TaskScheduler = TaskScheduler()

# for job in task_scheduler.scheduler.get_jobs():
#     job.modify(next_run_time=datetime.now())

with DatabaseConnection() as db:
    query = """SELECT time FROM misc_timers WHERE name = 'last_labra_message'"""
    result = db.execute_query(query)

    if result:
        last_labra_message = result[0]['time']
    else:
        now = datetime.utcnow()
        query = """INSERT INTO misc_timers (name, time) VALUES(%s, %s)"""
        values = ['last_labra_message', datetime.utcnow()]
        result = db.execute_query(query, values)
        last_labra_message = now

labra_typing = False

user_ping_tracking = {}

def is_admin_or_moderator():
    """Return whether the user is an Admin or a Moderator"""
    async def predicate(interaction: discord.Interaction):
        # Replace 'admin' and 'moderator' with the exact names of your roles
        allowed_roles = ['Admin', 'Mods']
        user_roles = [role.name for role in interaction.user.roles]
        if any(role in user_roles for role in allowed_roles):
            return True
        else:
            await interaction.response.send_message("You don't have the required role to use this command.", ephemeral=True)
            return False
    return app_commands.check(predicate)


def is_user_in_list(allowed_user_ids):
    """Return whether the user is in a list of user ids"""
    def predicate(interaction: discord.Interaction):
        if interaction.user.id in allowed_user_ids:
            return True
        else:
            interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return False
    return app_commands.check(predicate)

class CustomGroup(discord.app_commands.Group):
            pass

labraGroup = CustomGroup(name="labra", description="Commands relating to Labra")
rickGroup = CustomGroup(name="rick", description="Exists purely for rick roll command")
keyGroup = CustomGroup(name="key", description="Commands for the game keys for giveaways")
conversionGroup = CustomGroup(name="convert", description="Commands for the converting units")

@client.event
async def on_ready():
    """On Ready event called when the Bot is finished initializing"""
    client.tree.add_command(labraGroup)
    client.tree.add_command(rickGroup)
    client.tree.add_command(keyGroup)
    client.tree.add_command(conversionGroup)

    # This copies the global commands over to your guild.
    client.tree.copy_global_to(guild=GUILD)
    await client.tree.sync(guild=GUILD)
    
    activity = discord.Activity(type=discord.ActivityType.watching, name="the humans")
    await client.change_presence(status=discord.Status.online, activity=activity)
    
    print("ready")


@client.event
async def on_message(message: discord.Message):
    """On Message event called when a user sends a message"""
    if message.author == client.user:
        return
    
    guild: discord.Guild = message.guild
    
    url_pattern = r"(https?://)?(www.)?(discord.(gg|io|me|li)|(discordapp.com/invite)|(discord.com/invite))/[^\s/]+?(?=\b)"
    invite_link = re.search(url_pattern, message.content)

    if invite_link:
        link = invite_link.group()
        author = message.author
        channel = message.channel
        content = message.content

        await message.delete()
        await author.timeout(discord.utils.utcnow() + timedelta(days=28))

        alert_channel: discord.TextChannel = guild.get_channel(1188600358092689518)
        await alert_channel.send(f"message deleted in {channel} from {author} because it contained {link}")
    
    if message.author == guild.get_member(397664205798637568) and not labra_typing:
        global last_labra_message
        now = datetime.utcnow()
        if last_labra_message + timedelta(hours=12) < now:
            text = f"Oh hai {message.author.nick}"
            input_gif_path = 'oh_hi.gif'
            output_gif_path = 'labra_greeting.gif'
            add_text_to_gif(input_gif_path, output_gif_path, text, 'impact.ttf', 20)

            # Create a File object from the path of the generated GIF
            file = File(output_gif_path, filename="labra_greeting.gif")

            # Send the message with the embed and the file
            try:
                await message.reply(file=file)
            except Exception as e:
                print(e)
                return

            with DatabaseConnection() as db:
                query = """INSERT INTO misc_timers (name, time) VALUES(%s, %s) ON DUPLICATE KEY UPDATE time = VALUES(time);"""
                values = ['last_labra_message', now]
                result = db.execute_query(query, values)
                last_labra_message = now
            
    if 'never gonna give you up' in message.content.lower():
        now = datetime.utcnow().astimezone()
        twenty_eight_days_from_now: datetime = now + timedelta(days=28)
        await message.author.timeout(twenty_eight_days_from_now)

    if message.content.lower() == "ping" and (not any(role.name.lower() == 'architect' for role in message.author.roles) or is_admin_or_moderator()):
        
        user_id = message.author.id
        current_time = datetime.utcnow()

        # Initialize user tracking if not already present
        if user_id not in user_ping_tracking:
            user_ping_tracking[user_id] = {'count': 0, 'cooldown': current_time + timedelta(minutes=5)}
        
        user_data = user_ping_tracking[user_id]
        
        # Check if user is in cooldown
        if user_data['count'] > 3 and user_data['cooldown'] and current_time < user_data['cooldown']:
            return

        # Increment command usage count
        user_data['count'] += 1
        user_data['cooldown'] = current_time + timedelta(minutes=5)
        
        # Check if usage count exceeds limit
        if user_data['count'] > 3 and not is_admin_or_moderator():
            # Apply a 5-minute cooldown
            user_data['cooldown'] = current_time + timedelta(minutes=5)
            # await message.reply("You've reached the ping usage limit. A 5-minute cooldown has been applied.")
            architect: discord.Role = guild.get_role(737655479974756493)
            await message.author.add_roles(architect)

            role_id = architect.id
            guild_id = guild.id

            job = client.task_scheduler.schedule_task(
                func=remove_role,
                duration='5m',
                args=[user_id, role_id, guild_id]
            )
        else:
            # Record the time before sending the message using datetime
            start_time = datetime.utcnow()

            # Send a response message
            response_message = await message.channel.send("Pong!")

            # Record the time after the message is sent using datetime
            end_time = datetime.utcnow()

            # Calculate the response time in milliseconds
            response_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds

            # Edit the response message to include the response time
            await response_message.edit(content=f"Pong! Response time: {response_time:.2f} ms")

        # Reset count and cooldown if cooldown period has passed
        if user_data['cooldown'] and current_time >= user_data['cooldown']:
            user_data['count'] = 1  # Reset to 1 to count this usage
            user_data['cooldown'] = None  # Remove cooldown


@client.event
async def on_typing(channel, user, when):
    """On Typing event is called when a user is typing in a text channel"""
    guild: discord.Message = channel.guild
    if user == guild.get_member(397664205798637568):
        global labra_typing
        labra_typing = True
        global last_labra_message
        now = datetime.utcnow()
        if last_labra_message + timedelta(hours=12) < now:
            text = f"Oh hai {user.nick}"
            input_gif_path = 'oh_hi.gif'
            output_gif_path = 'labra_greeting.gif'
            add_text_to_gif(input_gif_path, output_gif_path, text, 'impact.ttf', 20)

            # Create a File object from the path of the generated GIF
            file = File(output_gif_path, filename="labra_greeting.gif")

            # Send the message with the embed and the file
            try:
                await channel.send(file=file)
            except Exception as e:
                print(e)
                labra_typing = False
                return

            with DatabaseConnection() as db:
                query = """INSERT INTO misc_timers (name, time) VALUES (%s, %s) ON DUPLICATE KEY UPDATE time = VALUES(time);"""
                values = ['last_labra_message', now]
                result = db.execute_query(query, values)
                last_labra_message = now
                labra_typing = False

@client.tree.command()
@app_commands.rename(text_to_send='text', channel='channel')
@app_commands.describe(text_to_send='Text to send', channel='Channel to send the message to')
@is_user_in_list([233128300602458113])  # Replace with the allowed user IDs
async def send(interaction: discord.Interaction, text_to_send: str, channel: discord.TextChannel = None, message_id: str = None):
    """Sends the text to a specified channel, optionally replying to a message."""

    if channel is None:
        channel = interaction.channel

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.reply(text_to_send)
        except discord.NotFound:
            await interaction.response.send_message("Message to reply to was not found.", ephemeral=True)
            return
    else:
        await channel.send(text_to_send)

    # Acknowledge the interaction
    await interaction.response.send_message(f"Message sent to {channel.mention}.", ephemeral=True)

ureg = UnitRegistry()
Q_ = ureg.Quantity

def convert_units(value: float, from_unit: Enum, to_unit: Enum, precision: int):
    measurement = Q_(value, from_unit.value.pint_name)
    converted_measurement = measurement.to(to_unit.value.pint_name)
    from_name = from_unit.value.singular if measurement == 1.0 else from_unit.value.plural
    to_name = to_unit.value.singular if converted_measurement == 1.0 else to_unit.value.plural

    format_specifier = f".{precision}G"
    return f"{measurement.magnitude:{format_specifier}} {from_name} is {converted_measurement.magnitude:{format_specifier}} {to_name}"

class Unit():
    pint_name: str = None
    singular: str = None
    plural: str = None

    def __init__(self, pint_name: str, singular: str, plural: str):
        self.pint_name = pint_name
        self.singular = singular
        self.plural = plural

class TempEnum(Enum):
    Fahrenheit = Unit('degree_Fahrenheit', 'degree Fahrenheit', 'degrees Fahrenheit')
    Celsius = Unit('degree_Celsius', 'degree Celsius', 'degrees Celsius')
    kelvin = Unit('kelvin', 'kelvin', 'kelvin')

@app_commands.rename(from_unit='from', to_unit='to')
@conversionGroup.command()
async def temperature(interaction: discord.Interaction, temperature: float, from_unit: TempEnum, to_unit: TempEnum, decimals: int = 2):
    await interaction.response.send_message(convert_units(temperature, from_unit, to_unit, decimals))


class DistanceEnum(Enum):
    inch = Unit('inch', 'inch', 'inches')
    foot = Unit('foot', 'foot', 'feet')
    mile = Unit('mile', 'mile', 'miles')
    millimeter = Unit('millimeter', 'millimeter', 'millimeters')
    centimeter = Unit('centimeter', 'centimeter', 'centimeters')
    meter = Unit('meter', 'meter', 'meters')
    kilometer = Unit('kilometer', 'kilometer', 'kilometers')

@app_commands.rename(from_unit='from', to_unit='to')
@conversionGroup.command()
async def length(interaction: discord.Interaction, length: float, from_unit: DistanceEnum, to_unit: DistanceEnum, decimals: int = 2):
    await interaction.response.send_message(convert_units(length, from_unit, to_unit, decimals))


class SpeedEnum(Enum):
    miles_per_hour = Unit('mile/hour', 'mile per hour', 'miles per hour')
    kilometers_per_hour = Unit('kilometer/hour', 'kilometer per hour', 'kilometers per hour')
    meters_per_second = Unit('meter/second', 'meter per second', 'meters per second')
    feet_per_second = Unit('foot/second', 'foot per second', 'feet per second')

@app_commands.rename(from_unit='from', to_unit='to')
@conversionGroup.command()
async def speed(interaction: discord.Interaction, value: float, from_unit: SpeedEnum, to_unit: SpeedEnum, decimals: int = 2):
    await interaction.response.send_message(convert_units(value, from_unit, to_unit, decimals))


class VolumeEnum(Enum):
    liter = Unit('liter', 'liter', 'liters')
    milliliter = Unit('milliliter', 'milliliter', 'milliliters')
    gallon = Unit('gallon', 'gallon', 'gallons')
    quart = Unit('quart', 'quart', 'quarts')
    pint = Unit('pint', 'pint', 'pints')
    cubic_meter = Unit('cubic_meter', 'cubic meter', 'cubic meters')
    cubic_foot = Unit('cubic_foot', 'cubic foot', 'cubic feet')
    cubic_inch = Unit('cubic_inch', 'cubic inch', 'cubic inches')

@app_commands.rename(from_unit='from', to_unit='to')
@conversionGroup.command()
async def volume(interaction: discord.Interaction, value: float, from_unit: VolumeEnum, to_unit: VolumeEnum, decimals: int = 2):
    await interaction.response.send_message(convert_units(value, from_unit, to_unit, decimals))


class Staff():
    singular: str = None
    plural: str = None
    conversion_factor: float = 0

    def __init__(self, singular: str, plural: str, conversion_factor: float):
        self.singular = singular
        self.plural = plural
        self.conversion_factor = conversion_factor

class StaffEnum(Enum):
    Joe = Staff("Joe", "Joes", 11)
    Sibby = Staff("Sibby", "Sibbies", 8.5)
    Palfly = Staff("Palfly", "Palflies", 8.1)
    Apoc = Staff("Apoc", "Apocalypti", 8.2)
    Kat = Staff("Kat", "Kats", 6.5)
    Tez = Staff("Tez", "Tezzes", 4)
    Sam = Staff("Sammy", "Sammies", 2.76381)
    
@app_commands.rename(from_unit='from', to_unit='to')
@conversionGroup.command()
async def staff(interaction: discord.Interaction, value: float, from_unit: StaffEnum, to_unit: StaffEnum, decimals: int = 2):
    converted_value = round(value * from_unit.value.conversion_factor / to_unit.value.conversion_factor, decimals)
    await interaction.response.send_message(f"{value} {from_unit.value.singular if value == 1.0 else from_unit.value.plural} is {converted_value} {to_unit.value.singular if converted_value == 1.0 else to_unit.value.plural}")

@keyGroup.command()
@app_commands.describe(num_keys='The number of keys to get')
@is_admin_or_moderator()  # Apply the role check
async def get(interaction: discord.Interaction, num_keys: int):
    """Gets a number of game keys from the database and provides a system for marking them as redeemed"""
    key_manager = GameKeyManager()
    keys = key_manager.get_random_unredeemed_keys(num_keys)
    key_manager.close_connection()

    def create_button_callback(key, btn):
        async def button_click(btn_interaction: discord.Interaction):
            key_manager = GameKeyManager()
            success: bool = key_manager.mark_as_redeemed(key['game_key'])
            key_manager.close_connection()
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
        btn: ui.Button = ui.Button(custom_id=f"key{i}", label=f"{key['name']}: Mark Redeemed", style=discord.ButtonStyle.primary, row=i)
        view.add_item(btn)
        btn.callback = create_button_callback(key, btn)

    await interaction.response.send_message("Keys:", view=view, ephemeral=True)

@keyGroup.command()
@is_admin_or_moderator()  # Apply the role check
async def add(interaction: discord.Interaction, title: str, description: str, key: str):
    """Adds a key to the database"""
    key_manager = GameKeyManager()
    success: bool = key_manager.insert_game_key(name=title, description=description, game_key=key)
    key_manager.close_connection()

    if success:
        await interaction.response.send_message(f"{title} was added successfully", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred. Please try again", ephemeral=True)

@keyGroup.command()
@is_admin_or_moderator()  # Apply the role check
async def list(interaction: discord.Interaction):
    """Displays a list of all games we have keys for and their status"""
    key_manager = GameKeyManager()
    keys = key_manager.get_key_list()
    key_manager.close_connection()

    # if len(keys) > 0:
    paginated_view = PaginatedView(keys)
    await interaction.response.send_message(embed=paginated_view.get_page_embed(), view=paginated_view)
    # else:
    #     await interaction.response.send_message(f"An error occurred. Please try again", ephemeral=True)

@labraGroup.command()
@is_user_in_list([233128300602458113, 736583661326958672])  # Replace with the allowed user IDs
async def rename(interaction: discord.Interaction, name: str):
    """Fucks with Labra's username"""
    guild: discord.Guild = interaction.guild
    if guild is None:
        await interaction.response.send_message('This command can only be used in a server.')
        return

    member = guild.get_member(397664205798637568)
    if member is None:
        await interaction.response.send_message('Member not found.', ephemeral=True)
        return

    try:
        await member.edit(nick=name)
        
        embed: discord.Embed = discord.Embed(
            title="Labrafoolery Successful",
            description=f"Labra was successfully renamed {name}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Labra was renamed")
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden as e:
        await interaction.response.send_message(f"Forbidden: {e}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
async def remove_role(user_id, role_id, guild_id):
    """Removes the specified role from a user"""
    print(f"{user_id}, {role_id}, {guild_id}")
    guild = client.get_guild(guild_id)
    if guild is None:
        return
    
    member = guild.get_member(user_id)
    if member is None:
        return

    role = guild.get_role(role_id)
    if role is None:
        return

    await member.remove_roles(role)
    
@rickGroup.command()
async def roll(interaction: discord.Interaction):
    """Trolls the user by Rick Rolling themselves and then architecting them"""
    guild: discord.Guild = interaction.guild
    if guild is None:
        await interaction.response.send_message('This command can only be used in a server.')
        return
    
    try:
        if any(role.name.lower() == 'architect' for role in interaction.user.roles):
            await interaction.response.send_message(f"Forbidden: You can't Rick Roll you... Architect...", ephemeral=True)
            return
        
        architect: discord.Role = guild.get_role(737655479974756493)
        await interaction.user.add_roles(architect)
        
        await interaction.response.send_message('https://tenor.com/view/rick-roll-rick-ashley-never-gonna-give-you-up-gif-22113173', ephemeral=True)
        await interaction.channel.send(f"{interaction.user.display_name} let their curiosity get the better of them.")

        user_id = interaction.user.id
        role_id = architect.id
        guild_id = guild.id

        job = client.task_scheduler.schedule_task(
            func=remove_role,
            duration='1m',
            args=[user_id, role_id, guild_id]
        )

    except discord.Forbidden as e:
        await interaction.followup.send(f"Forbidden: {e}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@client.tree.command()
async def sub_count(interaction: discord.Interaction):
    """Replies with RCE's 'current' subcount rounded to the nearest 10k"""
    sub_count = youtube.get_sub_count()

    if sub_count >= 1_000_000:
        sub_count = f'{sub_count/1_000_000} million'

    await interaction.response.send_message(f'Real Civil Engineer currently has {sub_count} subscribers')


@labraGroup.command()
async def greet(interaction: discord.Interaction):
    """Says Hai to Labra"""
    guild: discord.Guild = interaction.guild
    if guild is None:
        await interaction.response.send_message('This command can only be used in a server.')
        return

    member = guild.get_member(397664205798637568)
    if member is None:
        await interaction.response.send_message('Member not found.', ephemeral=True)
        return

    text = f"Oh hai {member.nick}"
    input_gif_path = 'oh_hi.gif'
    output_gif_path = 'labra_greeting.gif'
    add_text_to_gif(input_gif_path, output_gif_path, text, 'impact.ttf', 20)

    # Create a File object from the path of the generated GIF
    file = File(output_gif_path, filename="labra_greeting.gif")

    # Send the message with the embed and the file
    await interaction.response.send_message(file=file)

client.run(TOKEN)
