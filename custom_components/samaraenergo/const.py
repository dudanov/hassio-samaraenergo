"""Константы интеграции СамараЭнерго"""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import selector

DOMAIN = "samaraenergo"

CALC_PREFIX = "calc_"
CONF_HEATING = "heating"
CONF_POSITION = "position"
CONF_STOVE = "stove"
CONF_TARIFF = "tariff"
ENERGY_COST_UNIT = "RUB/kWh"
TIME_ZONE = "Europe/Samara"

# Схемы опций селекторов конфигуратора калькулятора-тарификатора

CALC_INIT_SCHEMA = {
    CONF_POSITION: ["1", "2"],
    CONF_TARIFF: ["7", "8"],  # "9"], # трехтарифный режим исключен (баг сервиса)
}

CALC_CITY_SCHEMA = {
    CONF_HEATING: ["3", "4"],
    CONF_STOVE: ["5", "6"],
}


ATTR_CONFIG_ENTRY = "config_entry"
ATTR_CONSUMPTIONS = "consumptions"
ATTR_DATE = "date"

GET_PRICE_SERVICE_NAME = "get_price"
GET_PRICE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Required(ATTR_CONSUMPTIONS): vol.All(cv.ensure_list, [cv.positive_float]),
        vol.Optional(ATTR_DATE): cv.date,
    }
)
