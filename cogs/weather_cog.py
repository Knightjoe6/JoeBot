from typing import Optional
from geopy.geocoders import Nominatim
from geopy.location import Location
from discord.ext import commands
from discord.ext.commands import Cog, Bot
from discord import app_commands, Interaction, Member, Guild, Embed, Color
import openmeteo_requests

import requests_cache
# import pandas as pd
from retry_requests import retry


class WeatherCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.geolocator = Nominatim(user_agent="JoeBot/1.0")

        # # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = retry_session)
        self.forcast_url = "https://api.open-meteo.com/v1/forecast"

    def cooldown_for_everyone_but_admin(interaction: Interaction) -> Optional[app_commands.Cooldown]:
        if interaction.user.get_role(736594738496536676):
            return None
        return app_commands.Cooldown(1, 300.0)

    @app_commands.command()
    @app_commands.rename(location_string="location")
    @app_commands.checks.dynamic_cooldown(factory=cooldown_for_everyone_but_admin, key=lambda i: (i.guild_id, i.user.id))
    async def weather(self, interaction: Interaction, location_string: str, show_location: bool=False):
        location: Location = self.geolocator.geocode(location_string, exactly_one=True)
        if location is None:
            await interaction.response.send_message(content="Unable to find location.", ephemeral=True)
            return
        lat, lng = location.latitude, location.longitude
        params = {
            "latitude": lat,
            "longitude": lng,
            "minutely_15": "temperature_2m",
            "daily": ["temperature_2m_max", "temperature_2m_min"],
            "forecast_days": 1
        }
        responses = self.openmeteo.weather_api(self.forcast_url, params=params)
        response = responses[0]

        current = response.Minutely15()
        current_temp_c = current.Variables(0).Values(0)

        daily = response.Daily()
        max_temp_c = daily.Variables(0).Values(0)
        min_temp_c = daily.Variables(1).Values(0)

        # Convert temperatures to Fahrenheit
        current_temp_f = (9/5 * current_temp_c) + 32
        max_temp_f = (9/5 * max_temp_c) + 32
        min_temp_f = (9/5 * min_temp_c) + 32

        embed = Embed(
            title="Weather Report",
            description="Weather report" + (f" for {location.address})" if show_location else ""),
            color=Color.blue()
        )
        embed.add_field(name="Current Temperature", value=f"{current_temp_c:.2f}°C ({current_temp_f:.2f}°F)", inline=False)
        embed.add_field(name="Max Temperature", value=f"{max_temp_c:.2f}°C ({max_temp_f:.2f}°F)", inline=True)
        embed.add_field(name="Min Temperature", value=f"{min_temp_c:.2f}°C ({min_temp_f:.2f}°F)", inline=True)
        if show_location:
            embed.set_footer(text=f"Coordinates: ({lat}, {lng})")
        await interaction.response.send_message(content="Weather reponse sent", delete_after=5, ephemeral=True)
        await interaction.channel.send(embed=embed)

        

async def setup(bot: Bot):
    await bot.add_cog(WeatherCog(bot))
