import logging

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from samaraenergo.calc import ApiError

from .calculator import CalculatorCoordinator
from .const import (
    ATTR_CONFIG_ENTRY,
    ATTR_CONSUMPTIONS,
    ATTR_DATE,
    CALCULATE_SERVICE_NAME,
    CALCULATE_SERVICE_SCHEMA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up EnergyZero services."""

    async def _get_zones_costs(call: ServiceCall) -> ServiceResponse:
        entry = hass.config_entries.async_get_entry(call.data[ATTR_CONFIG_ENTRY])
        consumptions: list[float] = call.data[ATTR_CONSUMPTIONS]
        date = call.data.get(ATTR_DATE)

        assert entry
        coordinator = entry.runtime_data

        if not isinstance(coordinator, CalculatorCoordinator):
            raise ServiceValidationError("Поддерживаются только тарификаторы")

        try:
            price = await coordinator.api.request(*consumptions, date=date)

        except ValueError as e:
            raise ServiceValidationError(e)

        except ApiError as e:
            raise HomeAssistantError(e)

        return {"price": price}

    hass.services.async_register(
        DOMAIN,
        CALCULATE_SERVICE_NAME,
        _get_zones_costs,
        schema=CALCULATE_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
