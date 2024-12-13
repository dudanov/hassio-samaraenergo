"""Config flow for Erkc integration."""

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from erkc63 import AuthorizationError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client import Client, ErkcConfigData
from .const import CONF_ACCOUNTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.EMAIL,
                autocomplete="email",
            ),
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
                autocomplete="current-password",
            ),
        ),
    }
)


class ErkcConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Erkc."""

    VERSION = 1

    _api: Client
    """Клиент"""
    _config: ErkcConfigData
    """Данные записи конфигурации"""
    _accounts: list[SelectOptionDict]
    """Список доступных лицевых счетов"""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            email, password = user_input[CONF_EMAIL].lower(), user_input[CONF_PASSWORD]

            await self.async_set_unique_id(email, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            try:
                self._api = Client(self.hass, email, password)
                self._accounts = await self._api.get_accounts_options()

            except AuthorizationError:
                errors["base"] = "invalid_credentials"

            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

            except Exception:
                errors["base"] = "unknown"

            else:
                if not self._accounts:
                    return self.async_abort(reason="no_accounts")

                self._config = ErkcConfigData(
                    email=email, password=password, accounts=[]
                )

                return await self.async_step_accounts()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_accounts(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the accounts step."""

        if user_input is not None:
            # Сохраняем идентификаторы выбранных лицевых счетов как `list[int]`.
            self._config[CONF_ACCOUNTS] = list(map(int, user_input[CONF_ACCOUNTS]))
            # Заголовок записи конфигурации - адрес почты.
            email = self._config[CONF_EMAIL]

            return self.async_create_entry(
                title=email,
                data=self._config,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNTS): SelectSelector(
                    SelectSelectorConfig(options=self._accounts, multiple=True)
                ),
            }
        )

        return self.async_show_form(step_id=CONF_ACCOUNTS, data_schema=schema)
