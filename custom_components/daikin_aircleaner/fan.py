from __future__ import annotations

import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_MODE_TO_LABEL = {
    "0": "手動",
    "1": "おまかせ",
    "2": "節電",
    "3": "花粉",
    "4": "のど/はだ",
    "5": "サーキュ",
}
_LABEL_TO_MODE = {v: k for k, v in _MODE_TO_LABEL.items()}


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
        FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
    )
    _attr_preset_modes = list(_MODE_TO_LABEL.values())
    _attr_preset_mode: str | None = None

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

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,
    ) -> None:
        await self._set({"pow": "1"})

    async def async_turn_off(self, **kwargs) -> None:
        await self._set({"pow": "0"})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode = _LABEL_TO_MODE.get(preset_mode)
        if mode is None:
            _LOGGER.error("Unknown preset mode: %s", preset_mode)
            return
        patch: dict = {"pow": "1", "mode": mode}
        if mode in ("1", "4"):  # おまかせ / のど/はだ は固定値
            patch.update({"airvol": "0", "humd": "4"})
        await self._set(patch)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        self._attr_preset_mode = _MODE_TO_LABEL.get(data.get("mode", ""))
        super()._handle_coordinator_update()

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
