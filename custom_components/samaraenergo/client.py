from __future__ import annotations

import asyncio
import functools
from typing import Awaitable, Callable, Concatenate, Iterable, TypedDict

from erkc63 import AccountInfo, ErkcClient
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectOptionDict


class ErkcConfigData(TypedDict):
    email: str
    password: str
    accounts: list[int]


type ClientMaker = Callable[[], ErkcClient]
type ClientMethod[T, **P] = Callable[Concatenate[Client, P], Awaitable[T]]


def get_account_options(accounts: Iterable[AccountInfo]) -> list[SelectOptionDict]:
    return [
        {"value": str(x.account), "label": f"{x.account}: {x.address}"}
        for x in accounts
    ]


def get_clientmaker(hass: HomeAssistant, email: str, password: str) -> ClientMaker:
    """Возвращает фабричную функцию создания клиента"""

    def _maker():
        return ErkcClient(
            login=email,
            password=password,
            session=async_get_clientsession(hass),
            close_connector=False,
        )

    return _maker


def session[T, **P](
    *, auth: bool
) -> Callable[[ClientMethod[T, P]], ClientMethod[T, P]]:
    """Декоратор вызова метода в открытой сессии"""

    def decorator(func: ClientMethod[T, P]):
        @functools.wraps(func)
        async def _wrapper(self: Client, *args: P.args, **kwargs: P.kwargs) -> T:
            # создаем клиент если еще не создан или соединение закрыто
            if not hasattr(self, "api") or self.api.connector_closed:
                self.api = self._make_api()

            async with self.api(auth=auth):
                return await func(self, *args, **kwargs)

        return _wrapper

    return decorator


class Client:
    """Клиент ЕРКЦ для HomeAssistant"""

    api: ErkcClient

    def __init__(self, hass: HomeAssistant, email: str, password: str) -> None:
        self._make_api = get_clientmaker(hass, email, password)

    @session(auth=True)
    async def get_accounts_options(self) -> list[SelectOptionDict]:
        """
        Запрашивает информацию по всем доступным лицевым счетам
        и возвращает список опций селектора.
        """

        accounts = await asyncio.gather(*map(self.api.account_info, self.api.accounts))

        return get_account_options(accounts)
