"""Sensor platform for Pellet Consumption Tracker integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    AUTONOMY_DAYS_WINDOW,
    DOMAIN,
    ICON_BAG,
    ICON_CALENDAR,
    ICON_EURO,
    ICON_PERCENTAGE,
    ICON_PELLET,
    ICON_SILO,
    SENSOR_DAILY_CONSUMPTION_BAGS,
    SENSOR_DAILY_CONSUMPTION_KG,
    SENSOR_ESTIMATED_AUTONOMY_DAYS,
    SENSOR_REMAINING_BAGS,
    SENSOR_REMAINING_KG,
    SENSOR_REMAINING_PERCENTAGE,
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


@dataclass(frozen=True, kw_only=True)
class PelletSensorEntityDescription(SensorEntityDescription):
    """Describes Pellet Consumption sensor entity."""

    value_fn: Callable[[dict], float | int | None] | None = None


SENSOR_DESCRIPTIONS: tuple[PelletSensorEntityDescription, ...] = (
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: PelletConsumptionCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PelletConsumptionSensor(
            coordinator=coordinator,
            description=description,
            entry_id=entry.entry_id,
        )
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class PelletConsumptionSensor(SensorEntity):
    """Representation of a Pellet Consumption sensor."""

    entity_description: PelletSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PelletConsumptionCoordinator,
        description: PelletSensorEntityDescription,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | int | None:
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

        return None


class PelletConsumptionCoordinator(DataUpdateCoordinator):
    """Coordinator to manage data updates."""

    def __init__(self, hass: HomeAssistant, entry_id: str, store_data: Callable[[], dict]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Pellet Consumption",
            update_interval=timedelta(minutes=15),
        )
        self.entry_id = entry_id
        self._store_data = store_data

        # Device info for all entities
        self.device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Pellet Consumption Tracker",
            "manufacturer": "@damienwolfer67",
            "model": "Pellet Tracker",
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
        data = self._store_data()

        silo_capacity = data.get(STORE_SILO_CAPACITY_BAGS, DEFAULT_SILO_CAPACITY_BAGS)
        current_bags = data.get(STORE_CURRENT_BAGS, silo_capacity)
        bag_weight = data.get(STORE_BAG_WEIGHT_KG, DEFAULT_BAG_WEIGHT_KG)
        pellet_price = data.get(STORE_PELLET_PRICE_EUR_KG, DEFAULT_PELLET_PRICE_EUR_KG)
        daily_snapshots = data.get(STORE_DAILY_SNAPSHOTS, {})
        recharge_history = data.get(STORE_RECHARGE_HISTORY, [])
        season_start = data.get(STORE_SEASON_START_DATE, date.today().isoformat())
        last_reset = data.get(STORE_LAST_RESET_DATE)

        today = date.today().isoformat()

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

    async def _async_midnight_reset(self, now: datetime) -> None:
        """Handle midnight reset for daily consumption tracking."""
        from . import async_middleware_update_snapshot

        await async_middleware_update_snapshot(self.hass, self.entry_id)
        await self.async_refresh()
        _LOGGER.info("Daily consumption reset and snapshot created")


# Import defaults to avoid circular import
from .const import (
    DEFAULT_BAG_WEIGHT_KG,
    DEFAULT_SILO_CAPACITY_BAGS,
    STORE_BAG_WEIGHT_KG,
    STORE_SILO_CAPACITY_BAGS,
)
import logging

_LOGGER = logging.getLogger(__name__)
