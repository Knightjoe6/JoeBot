from enum import Enum
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

class TempEnum(Enum):
    FAHRENHEIT = 'degree_Fahrenheit'
    CELSIUS = 'degree_Celsius'
    KELVIN = 'kelvin'

temp = Q_(70, TempEnum.FAHRENHEIT.value)

# Proper conversion to Celsius
temp_in_celsius = round(temp.to(TempEnum.CELSIUS.value).magnitude, 2)

print(temp_in_celsius)
