"""Micronova WiNET protocol handler for pellet stove communication."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Micronova WiNET endpoints
WINET_GET_REGISTERS = "/ajax/get-registers"
WINET_SET_REGISTER = "/ajax/set-register"

# Register addresses for common pellet stove functions
# These are based on the Thermorossi integration reverse engineering
REG_STATUS = 0x0000  # Operating status
REG_POWER = 0x0002   # Power level (1-5)
REG_FAN = 0x0003     # Fan speed (1-6)
REG_TEMP_AMBIENT = 0x0005  # Ambient temperature
REG_TEMP_SETPOINT = 0x0006  # Temperature setpoint
REG_ALARMS = 0x0007  # Alarm flags
REG_PELLETS_LOW = 0x0008  # Pellet reserve sensor

# Status values
STATUS_OFF = 0x00
STATUS_START = 0x01
STATUS_WORK = 0x02
STATUS_WAIT_ON = 0x03
STATUS_TEMP_OK = 0x04
STATUS_WAIT_TIME = 0x05
STATUS_STOP = 0x06
STATUS_SUNOUT = 0x07

STATUS_NAMES = {
    STATUS_OFF: "off",
    STATUS_START: "start",
    STATUS_WORK: "work",
    STATUS_WAIT_ON: "wait_on",
    STATUS_TEMP_OK: "temp_ok",
    STATUS_WAIT_TIME: "wait_time",
    STATUS_STOP: "stop",
    STATUS_SUNOUT: "sunout",
}

# Default consumption rates per power level (kg/hour)
# These can be overridden by user configuration
DEFAULT_CONSUMPTION_RATES = {
    1: 0.5,  # Power 1: ~0.5 kg/h
    2: 0.8,  # Power 2: ~0.8 kg/h
    3: 1.2,  # Power 3: ~1.2 kg/h
    4: 1.6,  # Power 4: ~1.6 kg/h
    5: 2.0,  # Power 5: ~2.0 kg/h
}


@dataclass
class MicronovaStoveState:
    """Data class for stove state."""

    status: str
    status_code: int
    power_level: int  # 0-5
    fan_speed: int | None  # 1-6
    ambient_temp: float | None
    setpoint_temp: float | None
    alarms: list[str]
    pellets_low: bool
    raw_data: dict[str, Any]


class MicronovaWinetError(Exception):
    """Exception raised for Micronova WiNET errors."""

    pass


class MicronovaWinetConnection:
    """Connection handler for Micronova WiNET module."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the connection.

        Args:
            host: IP address of the stove
            session: aiohttp ClientSession
        """
        self.host = host
        self.session = session
        self.base_url = f"http://{host}"
        self._is_on = None  # Cached ON/OFF state

    async def test_connection(self) -> bool:
        """Test if the stove is reachable."""
        try:
            data = await self.get_registers([REG_STATUS])
            return REG_STATUS in data
        except Exception as err:
            _LOGGER.warning("Failed to connect to Micronova WiNET: %s", err)
            return False

    async def get_registers(self, registers: list[int]) -> dict[int, int]:
        """Read multiple registers from the stove.

        Args:
            registers: List of register addresses to read

        Returns:
            Dictionary mapping register addresses to their values

        Raises:
            MicronovaWinetError: If communication fails
        """
        try:
            url = f"{self.base_url}{WINET_GET_REGISTERS}"
            params = {"r": ",".join(str(r) for r in registers)}

            async with asyncio.timeout(10):
                response = await self.session.get(url, params=params)
                response.raise_for_status()

                data = await response.json()

                # Parse response - format is typically {"r0": value, "r1": value, ...}
                result = {}
                for reg in registers:
                    key = f"r{reg}"
                    if key in data:
                        result[reg] = int(data[key])
                    else:
                        _LOGGER.debug("Register %s not found in response", reg)

                return result

        except asyncio.TimeoutError as err:
            raise MicronovaWinetError(f"Timeout reading registers: {err}") from err
        except aiohttp.ClientError as err:
            raise MicronovaWinetError(f"HTTP error reading registers: {err}") from err
        except Exception as err:
            raise MicronovaWinetError(f"Error reading registers: {err}") from err

    async def get_stove_state(self) -> MicronovaStoveState:
        """Get complete stove state.

        Returns:
            MicronovaStoveState with current stove data

        Raises:
            MicronovaWinetError: If communication fails
        """
        registers = [
            REG_STATUS,
            REG_POWER,
            REG_FAN,
            REG_TEMP_AMBIENT,
            REG_TEMP_SETPOINT,
            REG_ALARMS,
            REG_PELLETS_LOW,
        ]

        data = await self.get_registers(registers)

        # Parse status
        status_code = data.get(REG_STATUS, STATUS_OFF)
        status = STATUS_NAMES.get(status_code, "unknown")

        # Cache ON/OFF state
        self._is_on = status_code not in [STATUS_OFF, STATUS_STOP, STATUS_SUNOUT]

        # Parse power level (0-5)
        power_level = data.get(REG_POWER, 0)

        # Parse fan speed (1-6)
        fan_speed = data.get(REG_FAN)

        # Parse temperatures
        ambient_temp = data.get(REG_TEMP_AMBIENT)
        if ambient_temp is not None:
            ambient_temp = ambient_temp / 10  # Temperature is stored as integer * 10

        setpoint_temp = data.get(REG_TEMP_SETPOINT)
        if setpoint_temp is not None:
            setpoint_temp = setpoint_temp / 10

        # Parse alarms
        alarm_flags = data.get(REG_ALARMS, 0)
        alarms = []
        if alarm_flags:
            for i in range(16):
                if alarm_flags & (1 << i):
                    alarms.append(f"alarm_{i}")

        # Parse pellets low sensor
        pellets_low = bool(data.get(REG_PELLETS_LOW, 0))

        return MicronovaStoveState(
            status=status,
            status_code=status_code,
            power_level=power_level,
            fan_speed=fan_speed,
            ambient_temp=ambient_temp,
            setpoint_temp=setpoint_temp,
            alarms=alarms,
            pellets_low=pellets_low,
            raw_data=data,
        )

    @property
    def is_on(self) -> bool | None:
        """Return cached ON/OFF state."""
        return self._is_on


async def create_micronova_connection(
    hass: Any, host: str
) -> MicronovaWinetConnection:
    """Create a Micronova WiNET connection.

    Args:
        hass: Home Assistant instance
        host: IP address of the stove

    Returns:
        MicronovaWinetConnection instance
    """
    session = async_get_clientsession(hass)
    connection = MicronovaWinetConnection(host, session)

    # Test connection
    if not await connection.test_connection():
        raise MicronovaWinetError(f"Cannot connect to stove at {host}")

    _LOGGER.info("Successfully connected to Micronova WiNET at %s", host)
    return connection


def calculate_consumption_from_runtime(
    runtime_seconds: int,
    power_level: int,
    consumption_rates: dict[int, float] | None = None,
) -> float:
    """Calculate pellet consumption based on runtime and power level.

    Args:
        runtime_seconds: Time the stove has been running in seconds
        power_level: Current power level (1-5)
        consumption_rates: Optional custom consumption rates per power level (kg/h)

    Returns:
        Estimated consumption in kg
    """
    if power_level == 0 or runtime_seconds <= 0:
        return 0.0

    rates = consumption_rates or DEFAULT_CONSUMPTION_RATES
    rate = rates.get(power_level, 1.0)  # Default to 1.0 kg/h if unknown

    # Convert seconds to hours and multiply by rate
    hours = runtime_seconds / 3600
    return hours * rate


def estimate_daily_consumption_from_samples(
    samples: list[tuple[int, int]],  # (timestamp, power_level)
    consumption_rates: dict[int, float] | None = None,
) -> float:
    """Estimate daily consumption from power level samples.

    Args:
        samples: List of (timestamp, power_level) tuples
        consumption_rates: Optional custom consumption rates per power level (kg/h)

    Returns:
        Estimated consumption in kg for the period
    """
    if len(samples) < 2:
        return 0.0

    rates = consumption_rates or DEFAULT_CONSUMPTION_RATES
    total_consumption = 0.0

    for i in range(len(samples) - 1):
        timestamp1, power1 = samples[i]
        timestamp2, power2 = samples[i + 1]

        # Calculate time difference in hours
        duration_hours = (timestamp2 - timestamp1) / 3600

        # Use average power level during this period
        avg_power = (power1 + power2) / 2

        if avg_power > 0:
            rate = rates.get(int(avg_power), 1.0)
            total_consumption += duration_hours * rate

    return total_consumption
