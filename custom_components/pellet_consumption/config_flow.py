"""Config flow for Pellet Consumption Tracker integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CONSUMPTION_RATES,
    CONF_MICRONOVA_ENABLED,
    CONF_MICRONOVA_HOST,
    DEFAULT_BAG_WEIGHT_KG,
    DEFAULT_CONSUMPTION_RATES,
    DEFAULT_PELLET_PRICE_EUR_KG,
    DEFAULT_SILO_CAPACITY_BAGS,
    DOMAIN,
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # If Micronova is enabled, validate the connection
    if data.get(CONF_MICRONOVA_ENABLED) and data.get(CONF_MICRONOVA_HOST):
        from .micronova import create_micronova_connection

        try:
            await create_micronova_connection(hass, data[CONF_MICRONOVA_HOST])
        except Exception as err:
            raise ValueError(f"Cannot connect to Micronova stove: {err}") from err

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
            except ValueError as err:
                errors["base"] = "cannot_connect"
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
                vol.Optional(
                    CONF_MICRONOVA_ENABLED,
                    default=False,
                ): bool,
                vol.Optional(
                    CONF_MICRONOVA_HOST,
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
        """Manage the basic options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # If Micronova is being enabled, validate the connection
            if user_input.get(CONF_MICRONOVA_ENABLED) and user_input.get(CONF_MICRONOVA_HOST):
                from .micronova import create_micronova_connection

                try:
                    await create_micronova_connection(self.hass, user_input[CONF_MICRONOVA_HOST])
                except Exception as err:
                    errors["base"] = "cannot_connect"
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._get_init_schema(user_input),
                        errors=errors,
                    )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_init_schema(user_input),
            errors=errors,
        )

    def _get_init_schema(self, user_input: dict[str, Any] | None) -> vol.Schema:
        """Get the schema for the init step."""
        options = dict(self.config_entry.data)
        if self.config_entry.options:
            options.update(self.config_entry.options)

        # Use user_input if provided (for error handling)
        if user_input:
            options.update(user_input)

        return vol.Schema(
            {
                vol.Required(
                    "silo_capacity_bags",
                    default=options.get(
                        "silo_capacity_bags",
                        DEFAULT_SILO_CAPACITY_BAGS,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=1000),
                ),
                vol.Required(
                    "bag_weight_kg",
                    default=options.get(
                        "bag_weight_kg",
                        DEFAULT_BAG_WEIGHT_KG,
                    ),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=1, max=50),
                ),
                vol.Required(
                    "pellet_price_eur_kg",
                    default=options.get(
                        "pellet_price_eur_kg",
                        DEFAULT_PELLET_PRICE_EUR_KG,
                    ),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0, max=10),
                ),
                vol.Required(
                    CONF_MICRONOVA_ENABLED,
                    default=options.get(CONF_MICRONOVA_ENABLED, False),
                ): bool,
                vol.Optional(
                    CONF_MICRONOVA_HOST,
                    default=options.get(CONF_MICRONOVA_HOST, ""),
                ): str,
            }
        )

    async def async_step_micronova(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Micronova-specific options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = dict(self.config_entry.data)
        if self.config_entry.options:
            options.update(self.config_entry.options)

        # Get current consumption rates
        current_rates = options.get(CONF_CONSUMPTION_RATES, DEFAULT_CONSUMPTION_RATES)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    f"consumption_rate_1",
                    default=current_rates.get(1, 0.5),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.1, max=5.0),
                ),
                vol.Optional(
                    f"consumption_rate_2",
                    default=current_rates.get(2, 0.8),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.1, max=5.0),
                ),
                vol.Optional(
                    f"consumption_rate_3",
                    default=current_rates.get(3, 1.2),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.1, max=5.0),
                ),
                vol.Optional(
                    f"consumption_rate_4",
                    default=current_rates.get(4, 1.6),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.1, max=5.0),
                ),
                vol.Optional(
                    f"consumption_rate_5",
                    default=current_rates.get(5, 2.0),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0.1, max=5.0),
                ),
            }
        )

        return self.async_show_form(
            step_id="micronova",
            data_schema=data_schema,
        )
