import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util

from .calculator import CalculatorCoordinator
from .const import CALCULATE_SERVICE_NAME, CALCULATE_SERVICE_SCHEMA, DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up EnergyZero services."""

    async def _get_zones_costs(call: ServiceCall) -> ServiceResponse:
        date = dt_util.parse_date(call.data["date"])
        entry_id: str = call.data["config_entry"]
        entry: ConfigEntry[CalculatorCoordinator] | None = (
            hass.config_entries.async_get_entry(entry_id)
        )

        if entry is None or date is None:
            raise ServiceValidationError

        coordinator = entry.runtime_data

        if not isinstance(coordinator, CalculatorCoordinator):
            raise ServiceValidationError("Поддерживаются только тарификаторы")

        data = await coordinator.api.get_zones_cost(date=date)

        return {f"zone_{idx}": v for idx, v in enumerate(data, 1)}

    hass.services.async_register(
        DOMAIN,
        CALCULATE_SERVICE_NAME,
        _get_zones_costs,
        schema=CALCULATE_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
