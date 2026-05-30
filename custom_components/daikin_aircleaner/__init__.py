from __future__ import annotations

import asyncio
import logging
import urllib.parse

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_IP_ADDRESS, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN, Platform.BINARY_SENSOR]

_RETRY_DELAYS = (1, 2, 4)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = CleanerAPI(entry.data[CONF_IP_ADDRESS], async_get_clientsession(hass))

    async def async_update_data() -> dict:
        try:
            return await api.get()
        except Exception as err:
            raise UpdateFailed(err) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=DEFAULT_UPDATE_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class CleanerAPI:
    def __init__(self, address: str, session: aiohttp.ClientSession) -> None:
        self._address = address
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=5)

    async def _request(self, path: str, params: dict | None = None) -> str:
        url = f"http://{self._address}/cleaner/{path}"
        last_err: Exception
        for i, delay in enumerate((0, *_RETRY_DELAYS)):
            if delay:
                await asyncio.sleep(delay)
            try:
                async with self._session.get(url, params=params, timeout=self._timeout) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except Exception as err:
                last_err = err
                _LOGGER.debug("Request %s attempt %d failed: %s", path, i + 1, err)
        raise last_err

    async def get(self) -> dict:
        response: dict = {}
        for ep in ("get_control_info", "get_unit_status"):
            try:
                text = await self._request(ep)
            except Exception as err:
                _LOGGER.error("Failed to fetch %s: %s", ep, err)
                continue
            for pair in text.split(","):
                if "=" not in pair:
                    continue
                key, val = pair.split("=", 1)
                response[key] = urllib.parse.unquote(val, encoding="UTF-8")
        response.setdefault("led_dsp", "0")
        return response

    async def set(self, data: dict) -> str:
        try:
            return await self._request("set_control_info", params=data)
        except Exception as err:
            _LOGGER.error("Failed to set control info %s: %s", data, err)
            return ""
