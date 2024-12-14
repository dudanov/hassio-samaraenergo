"""Config flow for SamaraEnergo integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from samaraenergo.calc import CalculatorConfig

from .const import (
    CALC_CITY_SCHEMA,
    CALC_INIT_SCHEMA,
    CONF_HEATING,
    CONF_POSITION,
    CONF_STOVE,
    CONF_TARIFF,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _calc_schema(schema: dict[str, list[str]]):
    return vol.Schema(
        {
            vol.Required(key): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="calc_options",
                )
            )
            for key, options in schema.items()
        }
    )


class SamaraEnergoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SamaraEnergo."""

    VERSION = 1

    _config: str
    """Данные записи конфигурации"""

    async def _create_calc_entry(self) -> ConfigFlowResult:
        await self.async_set_unique_id(f"calc:{self._config}", raise_on_progress=False)
        self._abort_if_unique_id_configured()

        config = CalculatorConfig.from_config_str(self._config)

        return self.async_create_entry(title=f"Тарификатор {config.short_ru}", data={})

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        return await self.async_step_calc_init()

    async def async_step_calc_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the calc init options select step."""

        if user_input is not None:
            self._config = f"{user_input[CONF_POSITION]}{user_input[CONF_TARIFF]}"

            if self._config.startswith("1"):
                return await self.async_step_calc_city()

            return await self._create_calc_entry()

        return self.async_show_form(
            step_id="calc_init", data_schema=_calc_schema(CALC_INIT_SCHEMA)
        )

    async def async_step_calc_city(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the calc city options select step."""

        if user_input is not None:
            self._config += f"{user_input[CONF_HEATING]}{user_input[CONF_STOVE]}"
            return await self._create_calc_entry()

        return self.async_show_form(
            step_id="calc_city", data_schema=_calc_schema(CALC_CITY_SCHEMA)
        )
