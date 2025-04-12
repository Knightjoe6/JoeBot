#!/usr/bin/env python
import asyncio
import os

import discord
import dotenv

permissions = discord.Permissions()
permissions.create_instant_invite = False
permissions.kick_members = False
permissions.ban_members = False
permissions.administrator = False
permissions.manage_channels = False
permissions.manage_guild = False
permissions.add_reactions = True
permissions.view_audit_log = True
permissions.priority_speaker = False
permissions.stream = False
permissions.read_messages = True
permissions.send_messages = True
permissions.send_tts_messages = False
permissions.manage_messages = True
permissions.embed_links = True
permissions.attach_files = False
permissions.read_message_history = True
permissions.mention_everyone = False
permissions.external_emojis = True
permissions.view_guild_insights = False
permissions.connect = False
permissions.speak = False
permissions.mute_members = False
permissions.deafen_members = False
permissions.move_members = False
permissions.use_voice_activation = False
permissions.change_nickname = True
permissions.manage_nicknames = True
permissions.manage_roles = False
permissions.manage_webhooks = False
permissions.manage_expressions = False
permissions.use_application_commands = True
permissions.request_to_speak = False
permissions.manage_events = True
permissions.manage_threads = True
permissions.create_public_threads = True
permissions.create_private_threads = True
permissions.external_stickers = False
permissions.send_messages_in_threads = True
permissions.use_embedded_activities = False
permissions.moderate_members = True
permissions.view_creator_monetization_analytics = False
permissions.use_soundboard = False
permissions.create_expressions = False
permissions.create_events = True
permissions.use_external_sounds = False
permissions.send_voice_messages = False
permissions.send_polls = True
permissions.use_external_apps = False


async def main(token, guild_id):
    assert token, "Please set the DISCORD_TOKEN environment variable"

    client = discord.Client(intents=discord.Intents.default())
    async with client:
        await client.login(token)
        app_info = await client.application_info()
    client_id = app_info.id

    if guild_id:
        guild = discord.Object(guild_id)
    else:
        guild = discord.utils.MISSING

    print(discord.utils.oauth_url(client_id, guild=guild, permissions=permissions))


if __name__ == "__main__":
    dotenv.load_dotenv()
    asyncio.run(main(os.environ["DISCORD_TOKEN"], os.getenv("DISCORD_GUILD")))
