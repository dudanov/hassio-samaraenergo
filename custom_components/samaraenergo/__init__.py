"""The SamaraEnergo integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

type ErkcConfigEntry = ConfigEntry[None]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ErkcConfigEntry) -> bool:
    """Set up Duke Energy from a config entry."""

    # coordinator = ErkcCoordinator(hass, entry)
    # await coordinator.async_config_entry_first_refresh()
    # entry.runtime_data = coordinator

    _LOGGER.debug(f"Unique ID: {entry.unique_id}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ErkcConfigEntry) -> bool:
    """Unload a config entry."""
    return True
