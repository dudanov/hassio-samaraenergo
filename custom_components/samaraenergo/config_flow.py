"""Config flow for SamaraEnergo integration."""

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from samaraenergo.calc import ApiError, CalculatorConfig, OnlineCalculator

from .const import (
    CALC_CITY_SCHEMA,
    CALC_INIT_SCHEMA,
    CALC_PREFIX,
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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        return self.async_show_menu(step_id="user", menu_options=["calc_init"])

    ### БЛОК КОНФИГУРАТОРА КАЛЬКУЛЯТОРА ###

    async def async_step_calc_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the calc init options select step."""

        if user_input is not None:
            self._config = f"{user_input[CONF_POSITION]}{user_input[CONF_TARIFF]}"

            if self._config.startswith("1"):
                return await self.async_step_calc_city()

            return await self.async_step_calc_confirm()

        return self.async_show_form(
            step_id="calc_init", data_schema=_calc_schema(CALC_INIT_SCHEMA)
        )

    async def async_step_calc_city(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the calc city options select step."""

        if user_input is not None:
            self._config += f"{user_input[CONF_HEATING]}{user_input[CONF_STOVE]}"

            return await self.async_step_calc_confirm()

        return self.async_show_form(
            step_id="calc_city", data_schema=_calc_schema(CALC_CITY_SCHEMA)
        )

    async def async_step_calc_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the calc confirm step."""

        if user_input is not None:
            config = CalculatorConfig.from_string(self._config)

            return self.async_create_entry(title=f"Калькулятор {config.code}", data={})

        unique_id = f"{CALC_PREFIX}{self._config}"
        await self.async_set_unique_id(unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        self._set_confirm_only()

        api = OnlineCalculator.from_string(
            self._config,
            session=async_get_clientsession(self.hass),
        )
        code, cost = api.config.code, "-"

        try:
            cost = " | ".join(map(str, await api.get_zones_cost()))

        except (ClientError, TimeoutError):
            errors["base"] = "cannot_connect"

        except ApiError:
            errors["base"] = "api_error"

        except Exception:
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="calc_confirm",
            description_placeholders={"code": code, "zones_cost": cost},
            errors=errors,
        )

    ### КОНЕЦ БЛОКА КОНФИГУРАТОРА КАЛЬКУЛЯТОРА ###
