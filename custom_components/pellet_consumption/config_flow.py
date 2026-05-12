"""Config flow for Pellet Consumption Tracker integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_BAG_WEIGHT_KG,
    DEFAULT_PELLET_PRICE_EUR_KG,
    DEFAULT_SILO_CAPACITY_BAGS,
    DOMAIN,
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    return {
        "title": data.get("name", "Pellet Consumption"),
    }


class PelletConsumptionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pellet Consumption Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                # Set unique ID based on instance name to allow multiple instances
                await self.async_set_unique_id(
                    f"pellet_consumption_{user_input.get('name', 'default').lower().replace(' ', '_')}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception as err:
                errors["base"] = str(err)

        data_schema = vol.Schema(
            {
                vol.Required(
                    "silo_capacity_bags",
                    default=DEFAULT_SILO_CAPACITY_BAGS,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=1000),
                ),
                vol.Required(
                    "bag_weight_kg",
                    default=DEFAULT_BAG_WEIGHT_KG,
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=1, max=50),
                ),
                vol.Required(
                    "pellet_price_eur_kg",
                    default=DEFAULT_PELLET_PRICE_EUR_KG,
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0, max=10),
                ),
                vol.Optional(
                    "name",
                    default="",
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PelletConsumptionOptionsFlow(config_entry)


class PelletConsumptionOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(
                    "silo_capacity_bags",
                    default=options.get(
                        "silo_capacity_bags",
                        self.config_entry.data.get("silo_capacity_bags", DEFAULT_SILO_CAPACITY_BAGS),
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=1000),
                ),
                vol.Required(
                    "bag_weight_kg",
                    default=options.get(
                        "bag_weight_kg",
                        self.config_entry.data.get("bag_weight_kg", DEFAULT_BAG_WEIGHT_KG),
                    ),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=1, max=50),
                ),
                vol.Required(
                    "pellet_price_eur_kg",
                    default=options.get(
                        "pellet_price_eur_kg",
                        self.config_entry.data.get("pellet_price_eur_kg", DEFAULT_PELLET_PRICE_EUR_KG),
                    ),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0, max=10),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
