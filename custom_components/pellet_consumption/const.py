"""Constants for Pellet Consumption Tracker integration."""

from typing import Final

# Integration domain
DOMAIN: Final = "pellet_consumption"

# Default configuration values
DEFAULT_SILO_CAPACITY_BAGS: Final = 100  # Default silo capacity in bags
DEFAULT_BAG_WEIGHT_KG: Final = 15.0  # Default bag weight in kg
DEFAULT_PELLET_PRICE_EUR_KG: Final = 0.50  # Default price per kg in EUR

# Storage keys
STORAGE_KEY: Final = "pellet_consumption_storage"
STORAGE_VERSION: Final = 1

# Data store keys
STORE_SILO_CAPACITY_BAGS: Final = "silo_capacity_bags"
STORE_BAG_WEIGHT_KG: Final = "bag_weight_kg"
STORE_PELLET_PRICE_EUR_KG: Final = "pellet_price_eur_kg"
STORE_CURRENT_BAGS: Final = "current_bags"
STORE_RECHARGE_HISTORY: Final = "recharge_history"
STORE_SEASON_START_DATE: Final = "season_start_date"
STORE_DAILY_SNAPSHOTS: Final = "daily_snapshots"
STORE_LAST_RESET_DATE: Final = "last_reset_date"

# Sensor keys
SENSOR_DAILY_CONSUMPTION_BAGS: Final = "daily_consumption_bags"
SENSOR_DAILY_CONSUMPTION_KG: Final = "daily_consumption_kg"
SENSOR_REMAINING_BAGS: Final = "remaining_bags"
SENSOR_REMAINING_KG: Final = "remaining_kg"
SENSOR_REMAINING_PERCENTAGE: Final = "remaining_percentage"
SENSOR_ESTIMATED_AUTONOMY_DAYS: Final = "estimated_autonomy_days"
SENSOR_TOTAL_COST_SEASON: Final = "total_cost_season"

# Services
SERVICE_ADD_PELLETS: Final = "add_pellets"
SERVICE_SET_SILO_CAPACITY: Final = "set_silo_capacity"
SERVICE_SET_BAG_WEIGHT: Final = "set_bag_weight"
SERVICE_SET_PELLET_PRICE: Final = "set_pellet_price"
SERVICE_RESET_SEASON: Final = "reset_season"

# Service parameter keys
SERVICE_PARAM_BAGS: Final = "bags"
SERVICE_PARAM_WEIGHT: Final = "weight"
SERVICE_PARAM_PRICE: Final = "price"

# Icons
ICON_PELLET: Final = "mdi:fire"
ICON_SILO: Final = "mdi:silo"
ICON_BAG: Final = "mdi:package-variant"
ICON_EURO: Final = "mdi:currency-eur"
ICON_CALENDAR: Final = "mdi:calendar-clock"
ICON_PERCENTAGE: Final = "mdi:percent"

# Autonomy calculation
AUTONOMY_DAYS_WINDOW: Final = 7  # Number of days to average for autonomy calculation

# Micronova AGUA IoT integration
CONF_MICRONOVA_ENABLED: Final = "micronova_enabled"
CONF_MICRONOVA_HOST: Final = "micronova_host"
CONF_CONSUMPTION_RATES: Final = "consumption_rates"

# Default consumption rates per power level (kg/h)
DEFAULT_CONSUMPTION_RATES: Final[dict[int, float]] = {
    1: 0.5,  # Power 1: ~0.5 kg/h
    2: 0.8,  # Power 2: ~0.8 kg/h
    3: 1.2,  # Power 3: ~1.2 kg/h
    4: 1.6,  # Power 4: ~1.6 kg/h
    5: 2.0,  # Power 5: ~2.0 kg/h
}

# Micronova sensor keys
SENSOR_STOVE_STATUS: Final = "stove_status"
SENSOR_STOVE_POWER_LEVEL: Final = "stove_power_level"
SENSOR_STOVE_AMBIENT_TEMP: Final = "stove_ambient_temp"
SENSOR_STOVE_SETPOINT_TEMP: Final = "stove_setpoint_temp"
SENSOR_STOVE_RUNTIME_TODAY: Final = "stove_runtime_today"
SENSOR_ESTIMATED_CONSUMPTION_STOVE: Final = "estimated_consumption_stove"
SENSOR_STOVE_ALARMS: Final = "stove_alarms"
SENSOR_STOVE_PELLETS_LOW: Final = "stove_pellets_low"

# Micronova icons
ICON_STOVE: Final = "mdi:fireplace"
ICON_THERMOMETER: Final = "mdi:thermometer"
ICON_THERMOMETER_LOW: Final = "mdi:thermometer-low"
ICON_POWER: Final = "mdi:fire"
ICON_ALERT: Final = "mdi:alert-circle"
ICON_CLOCK_ALERT: Final = "mdi:clock-alert"

# Micronova status names
MICRONOVA_STATUS_NAMES: Final[dict[int, str]] = {
    0: "off",
    1: "start",
    2: "work",
    3: "wait_on",
    4: "temp_ok",
    5: "wait_time",
    6: "stop",
    7: "sunout",
}
