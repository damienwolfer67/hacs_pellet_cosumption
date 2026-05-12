"""Sensor platform for Pellet Consumption Tracker integration."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    AUTONOMY_DAYS_WINDOW,
    CONF_CONSUMPTION_RATES,
    CONF_MICRONOVA_ENABLED,
    CONF_MICRONOVA_HOST,
    DEFAULT_BAG_WEIGHT_KG,
    DEFAULT_CONSUMPTION_RATES,
    DEFAULT_PELLET_PRICE_EUR_KG,
    DEFAULT_SILO_CAPACITY_BAGS,
    DOMAIN,
    ICON_ALERT,
    ICON_BAG,
    ICON_CALENDAR,
    ICON_CLOCK_ALERT,
    ICON_EURO,
    ICON_PERCENTAGE,
    ICON_PELLET,
    ICON_POWER,
    ICON_SILO,
    ICON_STOVE,
    ICON_THERMOMETER,
    ICON_THERMOMETER_LOW,
    MICRONOVA_STATUS_NAMES,
    SENSOR_DAILY_CONSUMPTION_BAGS,
    SENSOR_DAILY_CONSUMPTION_KG,
    SENSOR_ESTIMATED_AUTONOMY_DAYS,
    SENSOR_ESTIMATED_CONSUMPTION_STOVE,
    SENSOR_REMAINING_BAGS,
    SENSOR_REMAINING_KG,
    SENSOR_REMAINING_PERCENTAGE,
    SENSOR_STOVE_ALARMS,
    SENSOR_STOVE_AMBIENT_TEMP,
    SENSOR_STOVE_PELLETS_LOW,
    SENSOR_STOVE_POWER_LEVEL,
    SENSOR_STOVE_RUNTIME_TODAY,
    SENSOR_STOVE_SETPOINT_TEMP,
    SENSOR_STOVE_STATUS,
    SENSOR_TOTAL_COST_SEASON,
    STORE_BAG_WEIGHT_KG,
    STORE_CURRENT_BAGS,
    STORE_DAILY_SNAPSHOTS,
    STORE_LAST_RESET_DATE,
    STORE_PELLET_PRICE_EUR_KG,
    STORE_RECHARGE_HISTORY,
    STORE_SEASON_START_DATE,
    STORE_SILO_CAPACITY_BAGS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PelletSensorEntityDescription(SensorEntityDescription):
    """Describes Pellet Consumption sensor entity."""

    value_fn: Callable[[dict], float | int | str | None] | None = None


# Base sensors (always available)
BASE_SENSOR_DESCRIPTIONS: tuple[PelletSensorEntityDescription, ...] = (
    PelletSensorEntityDescription(
        key=SENSOR_DAILY_CONSUMPTION_BAGS,
        name="Daily Consumption (bags)",
        icon=ICON_BAG,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="bags",
    ),
    PelletSensorEntityDescription(
        key=SENSOR_DAILY_CONSUMPTION_KG,
        name="Daily Consumption (kg)",
        icon=ICON_PELLET,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfMass.KILOGRAM,
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_REMAINING_BAGS,
        name="Remaining Pellets (bags)",
        icon=ICON_SILO,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="bags",
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_REMAINING_KG,
        name="Remaining Pellets (kg)",
        icon=ICON_SILO,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAM,
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_REMAINING_PERCENTAGE,
        name="Remaining Pellets (%)",
        icon=ICON_PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_ESTIMATED_AUTONOMY_DAYS,
        name="Estimated Autonomy",
        icon=ICON_CALENDAR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="days",
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_TOTAL_COST_SEASON,
        name="Total Cost (season)",
        icon=ICON_EURO,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="EUR",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
    ),
)

# Micronova stove sensors (only when enabled)
MICRONOVA_SENSOR_DESCRIPTIONS: tuple[PelletSensorEntityDescription, ...] = (
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_STATUS,
        name="Stove Status",
        icon=ICON_STOVE,
        device_class=SensorDeviceClass.ENUM,
        options=list(MICRONOVA_STATUS_NAMES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_POWER_LEVEL,
        name="Stove Power Level",
        icon=ICON_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="level",
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_AMBIENT_TEMP,
        name="Stove Ambient Temperature",
        icon=ICON_THERMOMETER,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_SETPOINT_TEMP,
        name="Stove Setpoint Temperature",
        icon=ICON_THERMOMETER_LOW,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_RUNTIME_TODAY,
        name="Stove Runtime Today",
        icon=ICON_CLOCK_ALERT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_ESTIMATED_CONSUMPTION_STOVE,
        name="Estimated Consumption (stove)",
        icon=ICON_PELLET,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfMass.KILOGRAM,
        suggested_display_precision=1,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_ALARMS,
        name="Stove Alarms",
        icon=ICON_ALERT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PelletSensorEntityDescription(
        key=SENSOR_STOVE_PELLETS_LOW,
        name="Stove Pellets Low",
        icon=ICON_ALERT,
        device_class=SensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Get or create coordinator
    if "coordinator" not in hass.data[DOMAIN][entry.entry_id]:
        # Create coordinator
        coordinator = PelletConsumptionCoordinator(
            hass=hass,
            entry_id=entry.entry_id,
            entry_data=hass.data[DOMAIN][entry.entry_id]["entry_data"],
            store_data=lambda: hass.data[DOMAIN][entry.entry_id]["data"],
            save_data=lambda data: hass.data[DOMAIN][entry.entry_id].update({"data": data}),
        )
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    coordinator: PelletConsumptionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        PelletConsumptionSensor(
            coordinator=coordinator,
            description=description,
            entry_id=entry.entry_id,
        )
        for description in BASE_SENSOR_DESCRIPTIONS
    ]

    # Add Micronova sensors if enabled
    if coordinator.micronova_enabled:
        entities.extend(
            [
                PelletConsumptionSensor(
                    coordinator=coordinator,
                    description=description,
                    entry_id=entry.entry_id,
                )
                for description in MICRONOVA_SENSOR_DESCRIPTIONS
            ]
        )

    async_add_entities(entities)


class PelletConsumptionSensor(SensorEntity):
    """Representation of a Pellet Consumption sensor."""

    entity_description: PelletSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: "PelletConsumptionCoordinator",
        description: PelletSensorEntityDescription,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        key = self.entity_description.key

        if key == SENSOR_DAILY_CONSUMPTION_BAGS:
            return data.get("daily_consumption_bags")
        elif key == SENSOR_DAILY_CONSUMPTION_KG:
            return data.get("daily_consumption_kg")
        elif key == SENSOR_REMAINING_BAGS:
            return data.get("remaining_bags")
        elif key == SENSOR_REMAINING_KG:
            return data.get("remaining_kg")
        elif key == SENSOR_REMAINING_PERCENTAGE:
            return data.get("remaining_percentage")
        elif key == SENSOR_ESTIMATED_AUTONOMY_DAYS:
            return data.get("estimated_autonomy_days")
        elif key == SENSOR_TOTAL_COST_SEASON:
            return data.get("total_cost_season")
        elif key == SENSOR_STOVE_STATUS:
            return data.get("stove_status")
        elif key == SENSOR_STOVE_POWER_LEVEL:
            return data.get("stove_power_level")
        elif key == SENSOR_STOVE_AMBIENT_TEMP:
            return data.get("stove_ambient_temp")
        elif key == SENSOR_STOVE_SETPOINT_TEMP:
            return data.get("stove_setpoint_temp")
        elif key == SENSOR_STOVE_RUNTIME_TODAY:
            return data.get("stove_runtime_today")
        elif key == SENSOR_ESTIMATED_CONSUMPTION_STOVE:
            return data.get("estimated_consumption_stove")
        elif key == SENSOR_STOVE_ALARMS:
            alarms = data.get("stove_alarms", [])
            return ",".join(alarms) if alarms else "OK"
        elif key == SENSOR_STOVE_PELLETS_LOW:
            return data.get("stove_pellets_low")

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Micronova sensors require connection to be available
        if self.entity_description.key in [d.key for d in MICRONOVA_SENSOR_DESCRIPTIONS]:
            return self.coordinator.micronova_connected
        return True


class PelletConsumptionCoordinator(DataUpdateCoordinator):
    """Coordinator to manage data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        entry_data: dict[str, Any],
        store_data: Callable[[], dict],
        save_data: Callable[[dict], Any],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Pellet Consumption",
            update_interval=timedelta(minutes=1),  # More frequent for Micronova
        )
        self.entry_id = entry_id
        self.entry_data = entry_data
        self._store_data = store_data
        self._save_data = save_data

        # Micronova settings
        self.micronova_enabled = entry_data.get(CONF_MICRONOVA_ENABLED, False)
        self.micronova_host = entry_data.get(CONF_MICRONOVA_HOST)
        self.consumption_rates = entry_data.get(CONF_CONSUMPTION_RATES, DEFAULT_CONSUMPTION_RATES)
        self.micronova_connected = False
        self._micronova_connection = None

        # Runtime tracking for today
        self._runtime_samples: list[tuple[int, int]] = []  # (timestamp, power_level)
        self._today_date = date.today()

        # Device info for all entities
        self.device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Pellet Consumption Tracker",
            "manufacturer": "@damienwolfer67",
            "model": "Pellet Tracker" + (" + Micronova" if self.micronova_enabled else ""),
        }

        # Track midnight for daily reset
        async_track_time_change(
            hass,
            self._async_midnight_reset,
            hour=0,
            minute=0,
            second=0,
        )

    async def _async_update_data(self) -> dict:
        """Update sensor data."""
        data = await self._update_base_data()

        # Update Micronova data if enabled
        if self.micronova_enabled and self.micronova_host:
            micronova_data = await self._update_micronova_data()
            data.update(micronova_data)

        return data

    async def _update_base_data(self) -> dict:
        """Update base sensor data (manual tracking)."""
        stored_data = self._store_data()

        silo_capacity = stored_data.get(STORE_SILO_CAPACITY_BAGS, DEFAULT_SILO_CAPACITY_BAGS)
        current_bags = stored_data.get(STORE_CURRENT_BAGS, silo_capacity)
        bag_weight = stored_data.get(STORE_BAG_WEIGHT_KG, DEFAULT_BAG_WEIGHT_KG)
        pellet_price = stored_data.get(STORE_PELLET_PRICE_EUR_KG, DEFAULT_PELLET_PRICE_EUR_KG)
        daily_snapshots = stored_data.get(STORE_DAILY_SNAPSHOTS, {})
        recharge_history = stored_data.get(STORE_RECHARGE_HISTORY, [])
        season_start = stored_data.get(STORE_SEASON_START_DATE, date.today().isoformat())
        last_reset = stored_data.get(STORE_LAST_RESET_DATE)

        today = date.today().isoformat()

        # Reset runtime samples on new day
        if self._today_date != date.today():
            self._runtime_samples = []
            self._today_date = date.today()

        # Calculate remaining
        remaining_bags = current_bags
        remaining_kg = current_bags * bag_weight
        remaining_percentage = (current_bags / silo_capacity * 100) if silo_capacity > 0 else 0

        # Calculate daily consumption
        daily_consumption_bags = 0.0
        daily_consumption_kg = 0.0

        if today in daily_snapshots:
            snapshot = daily_snapshots[today]
            start_bags = snapshot.get("start_bags", current_bags)
            consumed_today = start_bags - current_bags
            daily_consumption_bags = max(0, consumed_today)
            daily_consumption_kg = daily_consumption_bags * bag_weight

        # Calculate estimated autonomy (average over 7 days)
        estimated_autonomy_days = 0.0
        if remaining_bags > 0:
            total_consumed = 0.0
            days_with_data = 0

            for i in range(AUTONOMY_DAYS_WINDOW):
                check_date = (date.today() - timedelta(days=i)).isoformat()
                if check_date in daily_snapshots and check_date != today:
                    snapshot = daily_snapshots[check_date]
                    consumption = snapshot.get("consumed_bags", 0)
                    if consumption > 0:
                        total_consumed += consumption
                        days_with_data += 1

            if days_with_data > 0 and total_consumed > 0:
                avg_daily_consumption = total_consumed / days_with_data
                estimated_autonomy_days = remaining_bags / avg_daily_consumption
            else:
                # No history yet, estimate based on a default of 2 bags per day
                estimated_autonomy_days = remaining_bags / 2.0

        # Calculate total cost for the season
        total_cost_season = 0.0
        for recharge in recharge_history:
            if recharge.get("date", "") >= season_start:
                bags = recharge.get("bags", 0)
                total_cost_season += bags * bag_weight * pellet_price

        return {
            "daily_consumption_bags": round(daily_consumption_bags, 2),
            "daily_consumption_kg": round(daily_consumption_kg, 1),
            "remaining_bags": round(remaining_bags, 2),
            "remaining_kg": round(remaining_kg, 1),
            "remaining_percentage": round(remaining_percentage, 1),
            "estimated_autonomy_days": round(estimated_autonomy_days, 1),
            "total_cost_season": round(total_cost_season, 2),
        }

    async def _update_micronova_data(self) -> dict:
        """Update Micronova stove data."""
        from . import micronova

        data: dict[str, Any] = {}

        # Create connection if needed
        if self._micronova_connection is None:
            try:
                self._micronova_connection = await micronova.create_micronova_connection(
                    self.hass, self.micronova_host
                )
            except Exception as err:
                _LOGGER.warning("Failed to connect to Micronova: %s", err)
                self.micronova_connected = False
                return self._get_micronova_offline_data()

        try:
            # Get stove state
            stove_state = await self._micronova_connection.get_stove_state()
            self.micronova_connected = True

            # Store samples for consumption calculation
            timestamp = int(self.hass.loop.time())
            self._runtime_samples.append((timestamp, stove_state.power_level))

            # Keep only last 24 hours of samples (86400 seconds)
            cutoff = timestamp - 86400
            self._runtime_samples = [(t, p) for t, p in self._runtime_samples if t > cutoff]

            data.update({
                "stove_status": stove_state.status,
                "stove_power_level": stove_state.power_level,
                "stove_ambient_temp": stove_state.ambient_temp,
                "stove_setpoint_temp": stove_state.setpoint_temp,
                "stove_alarms": stove_state.alarms,
                "stove_pellets_low": stove_state.pellets_low,
            })

            # Calculate runtime today
            today_start = int(datetime.combine(date.today(), datetime.min.time()).timestamp())
            today_samples = [(t, p) for t, p in self._runtime_samples if t >= today_start]

            runtime_today = 0.0
            if len(today_samples) > 1:
                for i in range(len(today_samples) - 1):
                    duration = today_samples[i + 1][0] - today_samples[i][0]
                    if today_samples[i][1] > 0:  # Stove was on
                        runtime_today += duration

            data["stove_runtime_today"] = round(runtime_today / 3600, 1)  # Convert to hours

            # Calculate estimated consumption from stove
            data["estimated_consumption_stove"] = round(
                micronova.estimate_daily_consumption_from_samples(
                    today_samples, self.consumption_rates
                ),
                1,
            )

        except Exception as err:
            _LOGGER.warning("Error reading Micronova data: %s", err)
            self.micronova_connected = False
            return self._get_micronova_offline_data()

        return data

    def _get_micronova_offline_data(self) -> dict:
        """Return offline/unknown state for Micronova sensors."""
        return {
            "stove_status": "unknown",
            "stove_power_level": None,
            "stove_ambient_temp": None,
            "stove_setpoint_temp": None,
            "stove_alarms": [],
            "stove_pellets_low": None,
            "stove_runtime_today": None,
            "estimated_consumption_stove": None,
        }

    async def _async_midnight_reset(self, now: datetime) -> None:
        """Handle midnight reset for daily consumption tracking."""
        from . import async_middleware_update_snapshot

        await async_middleware_update_snapshot(self.hass, self.entry_id)

        # Reset runtime samples
        self._runtime_samples = []
        self._today_date = date.today()

        await self.async_refresh()
        _LOGGER.info("Daily consumption reset and snapshot created")
