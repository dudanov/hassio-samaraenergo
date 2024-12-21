"""Платформа сенсоров интеграции СамараЭнерго"""

from __future__ import annotations

import dataclasses as dc
import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .calculator import CalculatorCoordinator

_LOGGER = logging.getLogger(__name__)

_ZONE_COST = SensorEntityDescription(
    icon="mdi:currency-rub",
    key="",
    state_class=SensorStateClass.TOTAL,
    translation_key="zone_cost",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка платформы из записи конфигурации"""

    coordinator: CalculatorCoordinator = entry.runtime_data
    code = coordinator.api.config.code

    entities = [
        CalculatorSensorEntity(
            coordinator,
            dc.replace(
                _ZONE_COST,
                key=id,
                translation_placeholders={"code": code, "num": str(num)},
            ),
        )
        for num, id in enumerate(coordinator.entities_ids, 1)
    ]

    async_add_entities(entities)


class CalculatorSensorEntity(CoordinatorEntity[CalculatorCoordinator], SensorEntity):
    """Сущность сенсора тарификатора"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CalculatorCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        key = description.key
        self._attr_unique_id = key
        self.entity_description = description
        self.entity_id = f"sensor.{key}"
        self.key = key

        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработчик обновленных данных координатора"""

        data = self.coordinator.data

        if (value := data.get(self.key)) is not None:
            self._attr_native_value = value
            self.async_write_ha_state()
