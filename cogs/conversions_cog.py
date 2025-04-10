from discord.ext import commands
from discord import app_commands, Interaction
from discord.ext.commands import Bot
from discord.ext.commands.cog import Cog

from enum import Enum
from pint import UnitRegistry


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


class DistanceEnum(Enum):
    inch = Unit('inch', 'inch', 'inches')
    foot = Unit('foot', 'foot', 'feet')
    mile = Unit('mile', 'mile', 'miles')
    millimeter = Unit('millimeter', 'millimeter', 'millimeters')
    centimeter = Unit('centimeter', 'centimeter', 'centimeters')
    meter = Unit('meter', 'meter', 'meters')
    kilometer = Unit('kilometer', 'kilometer', 'kilometers')


class AreaEnum(Enum):
    sq_inch = Unit('inch**2', 'sq. inch', 'sq. inches')
    sq_foot = Unit('foot**2', 'sq. foot', 'sq. feet')
    sq_mile = Unit('mile**2', 'sq. mile', 'sq. miles')
    sq_millimeter = Unit('millimeter**2', 'sq. millimeter', 'sq. millimeters')
    sq_centimeter = Unit('centimeter**2', 'sq. centimeter', 'sq. centimeters')
    sq_meter = Unit('meter**2', 'sq. meter', 'sq. meters')
    sq_kilometer = Unit('kilometer**2', 'sq. kilometer', 'sq. kilometers')


class VolumeEnum(Enum):
    liter = Unit('liter', 'liter', 'liters')
    milliliter = Unit('milliliter', 'milliliter', 'milliliters')
    gallon = Unit('gallon', 'gallon', 'gallons')
    quart = Unit('quart', 'quart', 'quarts')
    pint = Unit('pint', 'pint', 'pints')
    cubic_meter = Unit('cubic_meter', 'cubic meter', 'cubic meters')
    cubic_foot = Unit('cubic_foot', 'cubic foot', 'cubic feet')
    cubic_inch = Unit('cubic_inch', 'cubic inch', 'cubic inches')


class SpeedEnum(Enum):
    miles_per_hour = Unit('mile/hour', 'mile per hour', 'miles per hour')
    kilometers_per_hour = Unit('kilometer/hour', 'kilometer per hour', 'kilometers per hour')
    meters_per_second = Unit('meter/second', 'meter per second', 'meters per second')
    feet_per_second = Unit('foot/second', 'foot per second', 'feet per second')


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


class ConversionsCog(commands.GroupCog, group_name="convert"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.ureg = UnitRegistry()
        self.Q_ = self.ureg.Quantity

    def convert_units(self, value: float, from_unit: Enum, to_unit: Enum, precision: int):
        measurement = self.Q_(value, from_unit.value.pint_name)
        converted_measurement = measurement.to(to_unit.value.pint_name)
        from_name = from_unit.value.singular if measurement == 1.0 else from_unit.value.plural
        to_name = to_unit.value.singular if converted_measurement == 1.0 else to_unit.value.plural

        format_specifier = f".{precision}G"
        return f"{measurement.magnitude:{format_specifier}} {from_name} is {converted_measurement.magnitude:{format_specifier}} {to_name}"

    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def temperature(self, interaction: Interaction, temperature: float, from_unit: TempEnum, to_unit: TempEnum, decimals: int = 5):
        await interaction.response.send_message(self.convert_units(temperature, from_unit, to_unit, decimals))

    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def length(self, interaction: Interaction, length: float, from_unit: DistanceEnum, to_unit: DistanceEnum, decimals: int = 5):
        await interaction.response.send_message(self.convert_units(length, from_unit, to_unit, decimals))

    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def area(self, interaction: Interaction, area: float, from_unit: AreaEnum, to_unit: AreaEnum, decimals: int = 5):
        await interaction.response.send_message(self.convert_units(area, from_unit, to_unit, decimals))

    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def volume(self, interaction: Interaction, value: float, from_unit: VolumeEnum, to_unit: VolumeEnum, decimals: int = 5):
        await interaction.response.send_message(self.convert_units(value, from_unit, to_unit, decimals))

    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def speed(self, interaction: Interaction, value: float, from_unit: SpeedEnum, to_unit: SpeedEnum, decimals: int = 5):
        await interaction.response.send_message(self.convert_units(value, from_unit, to_unit, decimals))
        
    @app_commands.rename(from_unit='from', to_unit='to')
    @app_commands.command()
    async def staff(self, interaction: Interaction, value: float, from_unit: StaffEnum, to_unit: StaffEnum, decimals: int = 5):
        converted_value = round(value * from_unit.value.conversion_factor / to_unit.value.conversion_factor, decimals)
        await interaction.response.send_message(f"{value} {from_unit.value.singular if value == 1.0 else from_unit.value.plural} is {converted_value} {to_unit.value.singular if converted_value == 1.0 else to_unit.value.plural}")

async def setup(bot):
    await bot.add_cog(ConversionsCog(bot))