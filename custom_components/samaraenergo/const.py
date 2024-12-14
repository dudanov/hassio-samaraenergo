"""Constants for the SamaraEnergo integration."""

DOMAIN = "samaraenergo"

CONF_HEATING = "heating"
CONF_POSITION = "position"
CONF_STOVE = "stove"
CONF_TARIFF = "tariff"

# Схемы опций селекторов конфигуратора калькулятора-тарификатора

CALC_INIT_SCHEMA = {
    CONF_POSITION: ["1", "2"],
    CONF_TARIFF: ["7", "8", "9"],
}

CALC_CITY_SCHEMA = {
    CONF_HEATING: ["3", "4"],
    CONF_STOVE: ["5", "6"],
}
