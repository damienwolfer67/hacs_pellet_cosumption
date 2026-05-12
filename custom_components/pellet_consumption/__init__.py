"""Pellet Consumption Tracker integration."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import (
    CONF_CONSUMPTION_RATES,
    CONF_MICRONOVA_ENABLED,
    CONF_MICRONOVA_HOST,
    DEFAULT_BAG_WEIGHT_KG,
    DEFAULT_CONSUMPTION_RATES,
    DEFAULT_PELLET_PRICE_EUR_KG,
    DEFAULT_SILO_CAPACITY_BAGS,
    DOMAIN,
    SERVICE_ADD_PELLETS,
    SERVICE_PARAM_BAGS,
    SERVICE_PARAM_PRICE,
    SERVICE_PARAM_WEIGHT,
    SERVICE_RESET_SEASON,
    SERVICE_SET_BAG_WEIGHT,
    SERVICE_SET_PELLET_PRICE,
    SERVICE_SET_SILO_CAPACITY,
    STORAGE_KEY,
    STORAGE_VERSION,
    STORE_BAG_WEIGHT_KG,
    STORE_CURRENT_BAGS,
    STORE_DAILY_SNAPSHOTS,
    STORE_LAST_RESET_DATE,
    STORE_PELLET_PRICE_EUR_KG,
    STORE_RECHARGE_HISTORY,
    STORE_SEASON_START_DATE,
    STORE_SILO_CAPACITY_BAGS,
)

PLATFORMS = (Platform.SENSOR,)


@dataclass
class PelletConsumptionData:
    """Data class for pellet consumption data."""

    silo_capacity_bags: int
    bag_weight_kg: float
    pellet_price_eur_kg: float
    current_bags: float
    recharge_history: list[dict[str, Any]]
    season_start_date: str
    daily_snapshots: dict[str, dict[str, Any]]
    last_reset_date: str | None
    micronova_enabled: bool = False
    micronova_host: str | None = None
    consumption_rates: dict[int, float] | None = None


type PelletConsumptionConfigEntry = ConfigEntry[PelletConsumptionData]


async def async_setup_entry(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> bool:
    """Set up Pellet Consumption Tracker from a config entry."""

    store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)

    # Load stored data or initialize with defaults
    stored_data = await store.async_load() or {}

    # Get configuration from entry data/options
    options = dict(entry.data)
    if entry.options:
        options.update(entry.options)

    silo_capacity_bags = options.get(
        "silo_capacity_bags",
        stored_data.get(STORE_SILO_CAPACITY_BAGS, DEFAULT_SILO_CAPACITY_BAGS),
    )
    bag_weight_kg = options.get(
        "bag_weight_kg",
        stored_data.get(STORE_BAG_WEIGHT_KG, DEFAULT_BAG_WEIGHT_KG),
    )
    pellet_price_eur_kg = options.get(
        "pellet_price_eur_kg",
        stored_data.get(STORE_PELLET_PRICE_EUR_KG, DEFAULT_PELLET_PRICE_EUR_KG),
    )
    micronova_enabled = options.get(CONF_MICRONOVA_ENABLED, False)
    micronova_host = options.get(CONF_MICRONOVA_HOST)
    consumption_rates = options.get(CONF_CONSUMPTION_RATES, DEFAULT_CONSUMPTION_RATES)

    # Initialize data
    data = PelletConsumptionData(
        silo_capacity_bags=silo_capacity_bags,
        bag_weight_kg=bag_weight_kg,
        pellet_price_eur_kg=pellet_price_eur_kg,
        current_bags=stored_data.get(STORE_CURRENT_BAGS, float(silo_capacity_bags)),
        recharge_history=stored_data.get(STORE_RECHARGE_HISTORY, []),
        season_start_date=stored_data.get(STORE_SEASON_START_DATE, date.today().isoformat()),
        daily_snapshots=stored_data.get(STORE_DAILY_SNAPSHOTS, {}),
        last_reset_date=stored_data.get(STORE_LAST_RESET_DATE),
        micronova_enabled=micronova_enabled,
        micronova_host=micronova_host,
        consumption_rates=consumption_rates,
    )

    entry.runtime_data = data

    # Store instance for later access
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "store": store,
        "data": data,
        "entry": entry,
        "entry_data": options,  # Store merged data for coordinator
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    _async_register_services(hass, entry)

    # Create initial snapshot if needed
    await _async_create_daily_snapshot(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Unregister services
        _async_unregister_services(hass)
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> bool:
    """Migrate old entry data."""
    if entry.version == 1:
        # No migration needed yet
        entry.version = 1

    return True


def _async_register_services(
    hass: HomeAssistant,
    entry: PelletConsumptionConfigEntry,
) -> None:
    """Register the Pellet Consumption services."""

    async def add_pellets_handler(call: ServiceCall) -> None:
        """Handle add_pellets service call."""
        data = hass.data[DOMAIN][entry.entry_id]["data"]
        bags_to_add = call.data.get(SERVICE_PARAM_BAGS, 0)

        if bags_to_add > 0:
            # Update current bags
            data.current_bags = min(
                data.current_bags + bags_to_add,
                data.silo_capacity_bags * 2,  # Allow temporary overflow
            )

            # Add to recharge history
            data.recharge_history.append(
                {
                    "date": datetime.now().isoformat(),
                    "bags": bags_to_add,
                    "kg": bags_to_add * data.bag_weight_kg,
                    "cost": bags_to_add * data.bag_weight_kg * data.pellet_price_eur_kg,
                }
            )

            # Save to store
            await _async_save_data(hass, entry)

            # Update sensors
            await _async_update_sensors(hass, entry)

            _LOGGER.info("Added %s bags of pellets. New total: %s bags", bags_to_add, data.current_bags)

    async def set_silo_capacity_handler(call: ServiceCall) -> None:
        """Handle set_silo_capacity service call."""
        data = hass.data[DOMAIN][entry.entry_id]["data"]
        new_capacity = call.data.get(SERVICE_PARAM_BAGS)

        if new_capacity and new_capacity > 0:
            data.silo_capacity_bags = new_capacity

            # Adjust current bags if needed
            if data.current_bags > new_capacity:
                data.current_bags = float(new_capacity)

            await _async_save_data(hass, entry)
            await _async_update_sensors(hass, entry)

            _LOGGER.info("Silo capacity set to %s bags", new_capacity)

    async def set_bag_weight_handler(call: ServiceCall) -> None:
        """Handle set_bag_weight service call."""
        data = hass.data[DOMAIN][entry.entry_id]["data"]
        new_weight = call.data.get(SERVICE_PARAM_WEIGHT)

        if new_weight and new_weight > 0:
            data.bag_weight_kg = new_weight
            await _async_save_data(hass, entry)
            await _async_update_sensors(hass, entry)

            _LOGGER.info("Bag weight set to %s kg", new_weight)

    async def set_pellet_price_handler(call: ServiceCall) -> None:
        """Handle set_pellet_price service call."""
        data = hass.data[DOMAIN][entry.entry_id]["data"]
        new_price = call.data.get(SERVICE_PARAM_PRICE)

        if new_price is not None and new_price >= 0:
            data.pellet_price_eur_kg = new_price
            await _async_save_data(hass, entry)
            await _async_update_sensors(hass, entry)

            _LOGGER.info("Pellet price set to %s EUR/kg", new_price)

    async def reset_season_handler(call: ServiceCall) -> None:
        """Handle reset_season service call."""
        data = hass.data[DOMAIN][entry.entry_id]["data"]

        # Reset seasonal data
        data.season_start_date = date.today().isoformat()
        data.recharge_history = []
        data.daily_snapshots = {}

        # Reset current bags to full capacity
        data.current_bags = float(data.silo_capacity_bags)

        await _async_save_data(hass, entry)
        await _async_update_sensors(hass, entry)

        _LOGGER.info("Season reset. New season started on %s", data.season_start_date)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PELLETS,
        add_pellets_handler,
        schema=vol.Schema({vol.Required(SERVICE_PARAM_BAGS): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000))}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SILO_CAPACITY,
        set_silo_capacity_handler,
        schema=vol.Schema({vol.Required(SERVICE_PARAM_BAGS): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000))}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BAG_WEIGHT,
        set_bag_weight_handler,
        schema=vol.Schema({vol.Required(SERVICE_PARAM_WEIGHT): vol.All(vol.Coerce(float), vol.Range(min=1, max=50))}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PELLET_PRICE,
        set_pellet_price_handler,
        schema=vol.Schema({vol.Required(SERVICE_PARAM_PRICE): vol.All(vol.Coerce(float), vol.Range(min=0, max=10))}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_SEASON,
        reset_season_handler,
        schema=vol.Schema({}),
    )


def _async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister the Pellet Consumption services."""
    hass.services.async_remove(DOMAIN, SERVICE_ADD_PELLETS)
    hass.services.async_remove(DOMAIN, SERVICE_SET_SILO_CAPACITY)
    hass.services.async_remove(DOMAIN, SERVICE_SET_BAG_WEIGHT)
    hass.services.async_remove(DOMAIN, SERVICE_SET_PELLET_PRICE)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_SEASON)


async def _async_save_data(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> None:
    """Save data to store."""
    data = hass.data[DOMAIN][entry.entry_id]["data"]
    store = hass.data[DOMAIN][entry.entry_id]["store"]

    await store.async_save(
        {
            STORE_SILO_CAPACITY_BAGS: data.silo_capacity_bags,
            STORE_BAG_WEIGHT_KG: data.bag_weight_kg,
            STORE_PELLET_PRICE_EUR_KG: data.pellet_price_eur_kg,
            STORE_CURRENT_BAGS: data.current_bags,
            STORE_RECHARGE_HISTORY: data.recharge_history,
            STORE_SEASON_START_DATE: data.season_start_date,
            STORE_DAILY_SNAPSHOTS: data.daily_snapshots,
            STORE_LAST_RESET_DATE: data.last_reset_date,
        }
    )


async def _async_update_sensors(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> None:
    """Trigger sensor updates."""
    # Refresh coordinator if it exists
    if "coordinator" in hass.data[DOMAIN][entry.entry_id]:
        hass.data[DOMAIN][entry.entry_id]["coordinator"].async_refresh()


async def _async_create_daily_snapshot(hass: HomeAssistant, entry: PelletConsumptionConfigEntry) -> None:
    """Create a daily snapshot for consumption tracking."""
    data = hass.data[DOMAIN][entry.entry_id]["data"]
    today = date.today().isoformat()

    if today not in data.daily_snapshots:
        data.daily_snapshots[today] = {
            "date": today,
            "start_bags": data.current_bags,
            "consumed_bags": 0.0,
        }
        await _async_save_data(hass, entry)


async def async_middleware_update_snapshot(hass: HomeAssistant, entry_id: str) -> None:
    """Update daily snapshot - called from sensor.py at midnight."""
    if entry_id not in hass.data.get(DOMAIN, {}):
        return

    entry = hass.data[DOMAIN][entry_id]["entry"]
    data = hass.data[DOMAIN][entry_id]["data"]
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Finalize yesterday's snapshot
    if yesterday in data.daily_snapshots:
        snapshot = data.daily_snapshots[yesterday]
        start_bags = snapshot.get("start_bags", data.current_bags)
        consumed = max(0, start_bags - data.current_bags)
        snapshot["consumed_bags"] = consumed

    # Create today's snapshot
    data.daily_snapshots[today] = {
        "date": today,
        "start_bags": data.current_bags,
        "consumed_bags": 0.0,
    }

    data.last_reset_date = today

    # Keep only last 365 days of snapshots
    cutoff_date = (date.today() - timedelta(days=365)).isoformat()
    data.daily_snapshots = {
        k: v for k, v in data.daily_snapshots.items() if k >= cutoff_date
    }

    await _async_save_data(hass, entry)
