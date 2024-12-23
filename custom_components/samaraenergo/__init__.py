"""Интеграция СамараЭнерго"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .calculator import CalculatorCoordinator
from .const import CALC_PREFIX
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Настройка интеграции СамараЭнерго"""

    async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка записи конфигурации интеграции СамараЭнерго"""

    assert (unique_id := entry.unique_id)
    coordinator = None

    if unique_id.startswith(CALC_PREFIX):
        coordinator = CalculatorCoordinator

    if coordinator is None:
        return False

    coordinator = coordinator(hass, entry)
    entry.runtime_data = coordinator

    # Platforms initialization
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
