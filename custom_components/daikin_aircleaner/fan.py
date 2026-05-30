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

_PRESET_MODES: list[str] = [
    "unknown",
    "手:風量自動-加湿無", "手:風量自動-加湿弱", "手:風量自動-加湿標準", "手:風量自動-加湿高",
    "手:風量弱-加湿無", "手:風量弱-加湿弱", "手:風量弱-加湿標準", "手:風量弱-加湿高",
    "手:風量標準-加湿無", "手:風量標準-加湿弱", "手:風量標準-加湿標準", "手:風量標準-加湿高",
    "手:風量高-加湿無", "手:風量高-加湿弱", "手:風量高-加湿標準", "手:風量高-加湿高",
    "手:風量最高-加湿無", "手:風量最高-加湿弱", "手:風量最高-加湿標準", "手:風量最高-加湿高",
    "おまかせ",
    "節電:加湿無", "節電:加湿弱", "節電:加湿標準", "節電:加湿高",
    "花粉:加湿無", "花粉:加湿弱", "花粉:加湿標準", "花粉:加湿高",
    "のど/はだ",
    "サーキュ:加湿無", "サーキュ:加湿弱", "サーキュ:加湿標準", "サーキュ:加湿高",
]

_AIRVOL_LABEL = {"0": "風量自動", "1": "風量弱", "2": "風量標準", "3": "風量高", "5": "風量最高"}
_HUMD_LABEL = {"0": "加湿無", "1": "加湿弱", "2": "加湿標準", "3": "加湿高"}


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
        self._attr_preset_mode = "unknown"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return data.get("pow") == "1"

    @property
    def preset_mode(self) -> str:
        return self._attr_preset_mode

    async def async_turn_on(self, **kwargs) -> None:
        await self._set({"pow": 1})

    async def async_turn_off(self, **kwargs) -> None:
        await self._set({"pow": 0})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        data: dict = {"pow": 1}
        if preset_mode == "おまかせ":
            data.update({"mode": "1", "airvol": "0", "humd": "4"})
        elif preset_mode == "のど/はだ":
            data.update({"mode": "4", "airvol": "0", "humd": "4"})
        else:
            if "手:" in preset_mode:
                data["mode"] = "0"
            elif "節電:" in preset_mode:
                data.update({"mode": "2", "airvol": "0"})
            elif "花粉:" in preset_mode:
                data.update({"mode": "3", "airvol": "0"})
            elif "サーキュ:" in preset_mode:
                data.update({"mode": "5", "airvol": "0"})
            for val, label in _AIRVOL_LABEL.items():
                if label in preset_mode:
                    data["airvol"] = val
                    break
            for val, label in _HUMD_LABEL.items():
                if label in preset_mode:
                    data["humd"] = val
                    break
        await self._set(data)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_preset_mode = self._calc_preset()
        self.async_write_ha_state()

    async def _set(self, data: dict) -> None:
        response = await self._api.set(data)
        if response and "ret=OK" in response:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set data: %s, response: %s", data, response)

    def _calc_preset(self) -> str:
        d = self.coordinator.data or {}
        mode = d.get("mode")
        airvol = d.get("airvol")
        humd = d.get("humd")

        if mode == "1":
            return "おまかせ"
        if mode == "4":
            return "のど/はだ"

        mode_prefix = {
            "0": "手", "2": "節電", "3": "花粉", "5": "サーキュ"
        }.get(mode)
        if mode_prefix is None:
            _LOGGER.debug("Unknown preset (mode:%s, airvol:%s, humd:%s)", mode, airvol, humd)
            return "unknown"

        humd_label = _HUMD_LABEL.get(humd or "", "")
        if mode == "0":
            airvol_label = _AIRVOL_LABEL.get(airvol or "", "")
            if airvol_label and humd_label:
                return f"手:{airvol_label}-{humd_label}"
        else:
            if humd_label:
                return f"{mode_prefix}:{humd_label}"

        _LOGGER.debug("Unknown preset (mode:%s, airvol:%s, humd:%s)", mode, airvol, humd)
        return "unknown"
