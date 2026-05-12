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
