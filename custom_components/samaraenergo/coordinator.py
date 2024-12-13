"""Coordinator to handle Duke Energy connections."""

import datetime as dt
import logging
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Any, cast

from aiohttp import ClientError
from erkc63 import ErkcClient
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type ErkcConfigEntry = ConfigEntry[ErkcCoordinator]


class ErkcCoordinator(DataUpdateCoordinator[None]):
    """Handle inserting statistics."""

    config_entry: ErkcConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ErkcConfigEntry,
    ) -> None:
        """Initialize the data handler."""

        super().__init__(
            hass,
            _LOGGER,
            name="Erkc",
            config_entry=entry,
            # Data is updated daily on Erkc.
            # Refresh every 12h to be at most 12h behind.
            update_interval=timedelta(hours=12),
        )

        self.api = ErkcClient(
            login=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
            session=async_create_clientsession(hass),
        )

        self._statistic_ids: set[str] = set()

        @callback
        def _dummy_listener() -> None:
            pass

        # Force the coordinator to periodically update by registering at least one listener.
        # Duke Energy does not provide forecast data, so all information is historical.
        # This makes _async_update_data get periodically called so we can insert statistics.
        self.async_add_listener(_dummy_listener)

        self.config_entry.async_on_unload(self._clear_statistics)

    def _clear_statistics(self) -> None:
        """Clear statistics."""
        get_instance(self.hass).async_clear_statistics(list(self._statistic_ids))

    async def _get_meters(self, account: int | None):
        meters = await self.api.meters_info(account=account)

        self._meters: dict[str, int] = {}

        for id, meter in meters.items():
            id_prefix = slugify(f"{meter.name}_{meter.serial}")
            self._meters[id_prefix] = id

            statistic_id = f"{DOMAIN}:meter_{id_prefix}"
            self._statistic_ids.add(statistic_id)

    async def _async_update_data(self) -> None:
        """Insert Erkc statistics."""

        meters = await self.api.meters_history()

        for meter in meters:
            id_prefix = slugify(f"{meter.name}_{meter.serial}")
            statistic_id = f"{DOMAIN}:{id_prefix}"
            self._statistic_ids.add(statistic_id)

            _LOGGER.debug(
                "Updating Statistics for %s",
                statistic_id,
            )

            last_stat = await get_instance(self.hass).async_add_executor_job(
                get_last_statistics,
                self.hass,
                1,
                statistic_id,
                True,
                set(),
            )

            if last_stat:
                usage = await self._async_get_energy_usage(
                    meter,
                    last_stat[statistic_id][0]["start"],
                )

                if not usage:
                    _LOGGER.debug("Нет новых данных. Пропуск обновления")
                    continue

                stats = await get_instance(self.hass).async_add_executor_job(
                    statistics_during_period,
                    self.hass,
                    min(usage.keys()),
                    None,
                    {statistic_id},
                    "hour",
                    None,
                    {"sum"},
                )

                consumption_sum = cast(float, stats[statistic_id][0]["sum"])
                last_stats_time = stats[statistic_id][0]["start"]

            else:
                _LOGGER.debug("Первоначальное обновление статистики")
                usage = await self._async_get_energy_usage(meter)
                consumption_sum = 0.0
                last_stats_time = None

            consumption_statistics = []

            for start, data in usage.items():
                if last_stats_time is not None and start.timestamp() <= last_stats_time:
                    continue
                consumption_sum += data["energy"]

                consumption_statistics.append(
                    StatisticData(
                        start=start, state=data["energy"], sum=consumption_sum
                    )
                )

            name_prefix = (
                f"Duke Energy {meter["serviceType"].capitalize()} {serial_number}"
            )
            consumption_metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name=f"{name_prefix} Consumption",
                source=DOMAIN,
                statistic_id=statistic_id,
                unit_of_measurement=(
                    UnitOfEnergy.KILO_WATT_HOUR
                    if meter["serviceType"] == "ELECTRIC"
                    else UnitOfVolume.CENTUM_CUBIC_FEET
                ),
            )

            _LOGGER.debug(
                "Adding %s statistics for %s",
                len(consumption_statistics),
                statistic_id,
            )
            async_add_external_statistics(
                self.hass, consumption_metadata, consumption_statistics
            )

    async def _async_get_energy_usage(
        self,
        meter: dict[str, Any],
        start: dt.date | None = None,
    ) -> dict[datetime, dict[str, float | int]]:
        """Get energy usage.

        If start_time is None, get usage since account activation (or as far back as possible),
        otherwise since start_time - 30 days to allow corrections in data.

        Duke Energy provides hourly data all the way back to ~3 years.
        """

        # Сервис ЕРКЦ обслуживает только город Сызрань в часовом поясе Europe/Samara
        tz = await dt_util.async_get_time_zone("Europe/Samara")
        lookback = timedelta(days=30)
        one = timedelta(days=1)

        await self.api.meters_history(start=start)

        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = dt_util.now(tz).replace(hour=0, minute=0, second=0, microsecond=0) - one
        _LOGGER.debug("Data lookup range: %s - %s", start, end)

        start_step = end - lookback
        end_step = end
        usage: dict[datetime, dict[str, float | int]] = {}
        while True:
            _LOGGER.debug("Getting hourly usage: %s - %s", start_step, end_step)
            try:
                # Get data
                results = await self.api.get_energy_usage(
                    meter["serialNum"], "HOURLY", "DAY", start_step, end_step
                )
                usage = {**results["data"], **usage}

                for missing in results["missing"]:
                    _LOGGER.debug("Missing data: %s", missing)

                # Set next range
                end_step = start_step - one
                start_step = max(start_step - lookback, start)

                # Make sure we don't go back too far
                if end_step < start:
                    break
            except (TimeoutError, ClientError):
                # ClientError is raised when there is no more data for the range
                break

        _LOGGER.debug("Got %s meter usage reads", len(usage))
        return usage
