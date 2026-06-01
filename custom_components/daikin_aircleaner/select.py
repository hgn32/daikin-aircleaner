from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_AIRVOL_TO_LABEL = {"0": "自動", "1": "弱", "2": "標準", "3": "高", "5": "最高"}
_LABEL_TO_AIRVOL = {v: k for k, v in _AIRVOL_TO_LABEL.items()}

_HUMD_TO_LABEL = {"0": "無", "1": "弱", "2": "標準", "3": "高"}
_LABEL_TO_HUMD = {v: k for k, v in _HUMD_TO_LABEL.items()}

_MODE_TO_LABEL = {
    "0": "手動",
    "1": "おまかせ",
    "2": "節電",
    "3": "花粉",
    "4": "のど/はだ",
    "5": "サーキュ",
}
_LABEL_TO_MODE = {v: k for k, v in _MODE_TO_LABEL.items()}
_VALID_AIRVOL = set(_AIRVOL_TO_LABEL.keys())  # {"0","1","2","3","5"}
_VALID_HUMD = set(_HUMD_TO_LABEL.keys())      # {"0","1","2","3"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ModeSelect(data["coordinator"], data["api"], entry),
        AirvolSelect(data["coordinator"], data["api"], entry),
        HumdSelect(data["coordinator"], data["api"], entry),
    ])


class _BaseSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry: ConfigEntry, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"aircleaner_{unique_suffix}_{entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name") or entry.title,
            manufacturer="Daikin",
            model="Aircleaner",
        )

    def _current_params(self) -> dict:
        d = self.coordinator.data or {}
        return {
            "pow":    d.get("pow", "1"),
            "mode":   d.get("mode", "0"),
            "airvol": d.get("airvol", "0"),
            "humd":   d.get("humd", "0"),
        }

    async def _set(self, patch: dict) -> None:
        data = {**self._current_params(), **patch}
        response = await self._api.set(data)
        if response and "ret=OK" in response:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set data: %s, response: %s", data, response)


class ModeSelect(_BaseSelect):
    _attr_translation_key = "mode"
    _attr_options = list(_MODE_TO_LABEL.values())

    def __init__(self, coordinator, api, entry):
        super().__init__(coordinator, api, entry, "mode")

    @property
    def current_option(self):
        mode = (self.coordinator.data or {}).get("mode")
        return _MODE_TO_LABEL.get(mode or "", None)

    async def async_select_option(self, option: str):
        mode = _LABEL_TO_MODE.get(option)
        if mode is None:
            _LOGGER.error("Unknown mode option: %s", option)
            return
        patch: dict = {"pow": "1", "mode": mode}
        if mode in ("1", "4"):   # おまかせ / のど/はだ: fixed params
            patch.update({"airvol": "0", "humd": "4"})
        elif mode == "0":        # 手動: restore last valid values
            d = self.coordinator.data or {}
            airvol = d.get("airvol", "0")
            humd   = d.get("humd", "0")
            if airvol not in _VALID_AIRVOL:
                airvol = "0"
            if humd not in _VALID_HUMD:
                humd = "0"
            patch.update({"airvol": airvol, "humd": humd})
        await self._set(patch)


class AirvolSelect(_BaseSelect):
    _attr_translation_key = "airvol"
    _attr_options = list(_AIRVOL_TO_LABEL.values())

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, "airvol")

    @property
    def available(self) -> bool:
        return (self.coordinator.data or {}).get("mode") == "0"

    @property
    def current_option(self) -> str | None:
        airvol = (self.coordinator.data or {}).get("airvol")
        return _AIRVOL_TO_LABEL.get(airvol or "", None)

    async def async_select_option(self, option: str) -> None:
        airvol = _LABEL_TO_AIRVOL.get(option)
        if airvol is None:
            _LOGGER.error("Unknown airvol option: %s", option)
            return
        await self._set({"airvol": airvol})


class HumdSelect(_BaseSelect):
    _attr_translation_key = "humd"
    _attr_options = list(_HUMD_TO_LABEL.values())

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, "humd")

    @property
    def available(self) -> bool:
        return (self.coordinator.data or {}).get("mode") == "0"

    @property
    def current_option(self) -> str | None:
        humd = (self.coordinator.data or {}).get("humd")
        return _HUMD_TO_LABEL.get(humd or "", None)

    async def async_select_option(self, option: str) -> None:
        humd = _LABEL_TO_HUMD.get(option)
        if humd is None:
            _LOGGER.error("Unknown humd option: %s", option)
            return
        await self._set({"humd": humd})
