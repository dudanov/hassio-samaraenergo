"""Константы интеграции СамараЭнерго"""

DOMAIN = "samaraenergo"

CALC_PREFIX = "calc_"
CONF_HEATING = "heating"
CONF_POSITION = "position"
CONF_STOVE = "stove"
CONF_TARIFF = "tariff"
ENERGY_COST_UNIT = "₽/кВт*ч"
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
