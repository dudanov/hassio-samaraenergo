"""Координатор тарификатора СамараЭнерго"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Mapping

from homeassistant.components.recorder.const import DOMAIN as RECORDER_DOMAIN
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify
from samaraenergo.calc import OnlineCalculator

from .const import CALC_PREFIX, DOMAIN, ENERGY_COST_UNIT, TIME_ZONE

type CalculatorUpdateData = Mapping[str, float]


_LOGGER = logging.getLogger(__name__)


class CalculatorCoordinator(DataUpdateCoordinator[CalculatorUpdateData]):
    """
    Координатор данных стоимости зон тарифа.

    Стоимость тарифов, как правило, обновляется 2 раза в год, но обновлять будем
    первого числа каждого месяца, так как месяца обновлений могут быть плавающие,
    да и изменение тарифов могут быть как чаще, так и реже.

    Ввиду таких больших периодов обновления не используем внутренний механизм
    координатора периодического опроса. Вместо этого подписываемся на событие
    изменения локального времени и вызываем метод `async_refresh` первого числа
    месяца для обновления.

    Координатор имеет встроенные механизмы обработки исключений запросов `aiohttp`,
    поэтому их обработку в методе обновления не применяем.
    """

    config_entry: ConfigEntry[CalculatorCoordinator]
    device_info: DeviceInfo
    entities_ids: list[str]

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry[CalculatorCoordinator]
    ) -> None:
        """Initialize the data handler."""

        assert (unique_id := entry.unique_id)

        self.api = OnlineCalculator.from_string(
            config=unique_id.removeprefix(CALC_PREFIX),
            session=async_get_clientsession(hass),
        )

        tariff = self.api.config.code

        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, unique_id)},
            manufacturer="СамараЭнерго",
            model="Онлайн-калькулятор",
            translation_key="calculator",
            translation_placeholders={"tariff": tariff},
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"Координатор калькулятора {tariff}",
            setup_method=self._se_setup,
            update_method=self._se_update,
        )

        # Вычисляем идентификаторы сенсоров
        self.entities_ids = []
        prefix_id = f"{DOMAIN}_tariff_{slugify(tariff)}_zone_"

        for n in range(1, self.api.zones + 1):
            self.entities_ids.append(f"{prefix_id}{n}")

        _LOGGER.debug("Идентификаторы сенсоров: %s", self.entities_ids)

        # Вызываем метод обновления тарифа ежедневно в начале суток
        entry.async_on_unload(
            async_track_time_change(
                hass,
                self._on_time_change,
                hour=0,
                minute=0,
                second=0,
            )
        )

        # Очистка статистики после выгрузки конфигурации
        def _clear_statistics():
            get_instance(hass).async_clear_statistics(
                [f"sensor.{x}" for x in self.entities_ids]
            )

        entry.async_on_unload(_clear_statistics)

    async def _on_time_change(self, datetime: dt.datetime):
        """Обработчик события изменения времени"""
        _LOGGER.debug("Событие изменения времени. Дата и время: %s", datetime)

        # Обновление ежемесячно в первый день месяца
        if datetime.day == 1:
            await self.async_refresh()

    async def _se_update(self) -> CalculatorUpdateData:
        """Метод получения обновленных данных"""

        _LOGGER.debug("Обновление данных координатора")

        tzinfo = await dt_util.async_get_time_zone(TIME_ZONE)
        data = await self.api.get_zones_cost(date=dt_util.now(tzinfo))
        data = dict(zip(self.entities_ids, data))

        _LOGGER.debug("Обновленные данные координатора: %s", data)

        return data

    async def _se_setup(self) -> None:
        """Метод получения обновленных данных"""

        tzinfo = await dt_util.async_get_time_zone(TIME_ZONE)
        statistic_id = f"sensor.{self.entities_ids[0]}"

        last_stat = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,
            statistic_id,
            False,
            set(),
        )

        if last_stat:
            if (start := last_stat[statistic_id][0].get("start")) is None:
                raise HomeAssistantError(
                    "Нет штампа времени начала в записи статистики"
                )

            start = dt.datetime.fromtimestamp(start, tzinfo)

            _LOGGER.debug("Дата и время последней записи статистики: %s", start)

            data = await self.api.get_last_months_costs(
                start,
                tzinfo=tzinfo,
                hourly_data=True,
            )

        else:
            _LOGGER.debug("Обновление статистики за последние 3 года")

            data = await self.api.get_last_months_costs(
                36,
                tzinfo=tzinfo,
                hourly_data=True,
            )

        if data is None:
            _LOGGER.debug("Нет новых данных для обновления статистики")
            return

        for entity, costs in zip(self.entities_ids, data):
            # Метаданные долгосрочной статистики
            metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name=None,
                source=RECORDER_DOMAIN,
                statistic_id=f"sensor.{entity}",
                unit_of_measurement=ENERGY_COST_UNIT,
            )

            values = [StatisticData(start=k, state=v, sum=v) for k, v in costs]

            _LOGGER.debug("Импорт данных статистики: %s", values)

            async_import_statistics(self.hass, metadata, values)
