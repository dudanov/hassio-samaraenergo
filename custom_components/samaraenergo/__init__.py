"""The SamaraEnergo integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calculator import CalculatorCoordinator
from .const import CALC_PREFIX

_LOGGER = logging.getLogger(__name__)

type SamaraEnergoConfigEntry[T: DataUpdateCoordinator] = ConfigEntry[T]


PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamaraEnergoConfigEntry[DataUpdateCoordinator[Any]],
) -> bool:
    """Set up SamaraEnergo from a config entry."""

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


async def async_unload_entry(
    hass: HomeAssistant, entry: SamaraEnergoConfigEntry[DataUpdateCoordinator[Any]]
) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
