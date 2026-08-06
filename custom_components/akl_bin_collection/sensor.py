"""Date sensors for Auckland Council bin collections."""

from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import collection_url
from .const import DOMAIN
from .coordinator import AucklandBinCollectionCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="rubbish",
        translation_key="rubbish",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:trash-can",
    ),
    SensorEntityDescription(
        key="recycling",
        translation_key="recycling",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:recycle",
    ),
    SensorEntityDescription(
        key="food_scraps",
        translation_key="food_scraps",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:food-apple",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up collection date sensors."""
    coordinator: AucklandBinCollectionCoordinator = entry.runtime_data
    async_add_entities(
        AucklandCollectionSensor(coordinator, description)
        for description in ENTITY_DESCRIPTIONS
    )


class AucklandCollectionSensor(
    CoordinatorEntity[AucklandBinCollectionCoordinator], SensorEntity
):
    """A next-collection date sensor."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Auckland Council"

    def __init__(
        self,
        coordinator: AucklandBinCollectionCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.property_id}_{description.key}"

    @property
    def native_value(self) -> date | None:
        """Return the next collection date."""
        return self.coordinator.data.date_for(self.entity_description.key)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the virtual service device for this property."""
        address = self.coordinator.data.address
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.property_id)},
            name=address or f"Auckland property {self.coordinator.property_id}",
            manufacturer="Auckland Council",
            configuration_url=collection_url(self.coordinator.property_id),
        )

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return useful source details."""
        return {
            "address": self.coordinator.data.address,
            "property_id": self.coordinator.property_id,
            "source_url": collection_url(self.coordinator.property_id),
        }
