"""Data update coordinator for Auckland collection dates."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AucklandCouncilApi, AucklandCouncilError, CollectionSchedule
from .const import CONF_PROPERTY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)
_UPDATE_INTERVAL = timedelta(hours=6)


class AucklandBinCollectionCoordinator(DataUpdateCoordinator[CollectionSchedule]):
    """Coordinate collection data updates for one property."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: AucklandCouncilApi,
    ) -> None:
        self.api = api
        self.property_id: str = config_entry.data[CONF_PROPERTY_ID]
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{self.property_id}",
            update_interval=_UPDATE_INTERVAL,
            always_update=False,
        )

    async def _async_update_data(self) -> CollectionSchedule:
        try:
            return await self.api.async_get_schedule(self.property_id)
        except AucklandCouncilError as err:
            raise UpdateFailed(
                f"Unable to update collection dates for {self.property_id}: {err}"
            ) from err
