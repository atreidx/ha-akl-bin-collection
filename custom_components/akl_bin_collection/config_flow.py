"""Config flow for Auckland Council Bin Collection."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AucklandCouncilApi,
    AucklandCouncilConnectionError,
    AucklandCouncilInvalidPropertyError,
    normalize_property_id,
)
from .const import CONF_PROPERTY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AucklandBinCollectionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle configuration for Auckland Council Bin Collection."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a property ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                property_id = normalize_property_id(user_input[CONF_PROPERTY_ID])
                schedule = await AucklandCouncilApi(
                    async_get_clientsession(self.hass)
                ).async_get_schedule(property_id)
            except AucklandCouncilInvalidPropertyError:
                errors["base"] = "invalid_property_id"
            except AucklandCouncilConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - keep config flow recoverable
                _LOGGER.exception("Unexpected error validating property ID")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(property_id)
                self._abort_if_unique_id_configured()
                title = schedule.address or f"Auckland property {property_id}"
                return self.async_create_entry(
                    title=title,
                    data={CONF_PROPERTY_ID: property_id},
                )

        default = ""
        if user_input is not None:
            default = str(user_input.get(CONF_PROPERTY_ID, ""))
        schema = vol.Schema({vol.Required(CONF_PROPERTY_ID, default=default): str})
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
