from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_IP_ADDRESS, DOMAIN

_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required("name"): str,
})


class DaikinAircleanerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_SCHEMA)

        errors = {}
        for entry in self._async_current_entries():
            if entry.data.get(CONF_IP_ADDRESS) == user_input[CONF_IP_ADDRESS]:
                return self.async_abort(reason="already_configured")
            if entry.data.get("name") == user_input["name"] or entry.title == user_input["name"]:
                errors["name"] = "name_exists"

        if errors:
            return self.async_show_form(step_id="user", data_schema=_SCHEMA, errors=errors)

        from . import CleanerAPI
        api = CleanerAPI(user_input[CONF_IP_ADDRESS], async_get_clientsession(self.hass))
        mac = await api.get_mac()
        if mac:
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()
            user_input["mac"] = mac

        return self.async_create_entry(title=user_input["name"], data=user_input)
