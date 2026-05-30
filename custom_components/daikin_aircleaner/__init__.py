from __future__ import annotations

import logging
import urllib.parse
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_IP_ADDRESS, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.data[CONF_IP_ADDRESS]
    session = async_get_clientsession(hass)
    api = CleanerAPI(address, session)

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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class CleanerAPI:
    def __init__(self, address: str, session: aiohttp.ClientSession) -> None:
        self._address = address
        self._session = session

    async def _fetch_path(self, path: str) -> str:
        url = f"http://{self._address}/cleaner/{path}"
        timeout = aiohttp.ClientTimeout(total=5)
        for attempt in range(1, 4):
            try:
                async with self._session.get(url, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except Exception:
                if attempt == 3:
                    raise
                import asyncio
                await asyncio.sleep(min(attempt * 1, 5))
        return ""

    async def get(self) -> dict:
        response: dict = {}
        for ep in ("get_control_info", "get_unit_status"):
            try:
                text = await self._fetch_path(ep)
            except Exception as err:
                _LOGGER.error("Failed to fetch %s: %s", ep, err)
                continue
            for pair_str in text.split(","):
                if "=" not in pair_str:
                    continue
                key, val = pair_str.split("=", 1)
                try:
                    response[key] = urllib.parse.unquote(val, encoding="UTF-8")
                except Exception:
                    response[key] = val
        response.setdefault("led_dsp", "0")
        return response

    async def set(self, data: dict) -> str:
        url = f"http://{self._address}/cleaner/set_control_info"
        timeout = aiohttp.ClientTimeout(total=5)
        for attempt in range(1, 4):
            try:
                async with self._session.get(url, params=data, timeout=timeout) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except Exception as err:
                _LOGGER.debug("set attempt %d failed: %s", attempt, err)
        _LOGGER.error("Failed to set control info after retries: %s", data)
        return ""
