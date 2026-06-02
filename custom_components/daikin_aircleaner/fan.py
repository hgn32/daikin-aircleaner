from __future__ import annotations

import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_MODE_TO_LABEL = {
    "1": "おまかせ",
    "2": "節電",
    "3": "花粉",
    "4": "のど/はだ",
    "5": "サーキュ",
}
_LABEL_TO_MODE = {v: k for k, v in _MODE_TO_LABEL.items()}

_VALID_AIRVOL = {"1", "2", "3", "5"}
_VALID_HUMD = {"0", "1", "2", "3"}

_PRESET_MODES = ["おまかせ", "風量自動", "手動", "節電", "花粉", "のど/はだ", "サーキュ"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([Aircleaner(data["coordinator"], data["api"], entry)])


class Aircleaner(CoordinatorEntity, FanEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = _PRESET_MODES

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"aircleaner_{entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name") or entry.title,
            manufacturer="Daikin",
            model="Aircleaner",
        )

    @property
    def is_on(self) -> bool:
        return (self.coordinator.data or {}).get("pow") == "1"

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data or {}
        airvol_map = {"1": "弱", "2": "標準", "3": "高", "5": "最高"}
        humd_map   = {"0": "無", "1": "弱", "2": "標準", "3": "高"}
        return {
            "airvol": airvol_map.get(d.get("airvol", ""), ""),
            "humd":   humd_map.get(d.get("humd", ""), ""),
        }

    @property
    def preset_mode(self) -> str | None:
        d = self.coordinator.data or {}
        mode = d.get("mode")
        if mode == "0":
            airvol = d.get("airvol", "0")
            return "風量自動" if airvol == "0" else "手動"
        return _MODE_TO_LABEL.get(mode or "", None)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,
    ) -> None:
        patch: dict = {"pow": "1"}
        if preset_mode is not None:
            await self._apply_mode(preset_mode, base=patch)
            return
        await self._set(patch)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set({"pow": "0"})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._apply_mode(preset_mode, base={"pow": "1"})

    async def _apply_mode(self, preset_mode: str, base: dict) -> None:
        if preset_mode == "風量自動":
            await self._set({**base, "mode": "0", "airvol": "0"})
            return
        if preset_mode == "手動":
            d = self.coordinator.data or {}
            airvol = d.get("airvol", "1")
            if airvol not in _VALID_AIRVOL:
                airvol = "1"
            humd = d.get("humd", "0")
            if humd not in _VALID_HUMD:
                humd = "0"
            await self._set({**base, "mode": "0", "airvol": airvol, "humd": humd})
            return
        mode = _LABEL_TO_MODE.get(preset_mode)
        if mode is None:
            _LOGGER.error("Unknown preset mode: %s", preset_mode)
            return
        await self._set({**base, "mode": mode})

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
