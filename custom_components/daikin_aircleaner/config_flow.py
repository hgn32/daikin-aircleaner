from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_IP_ADDRESS, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required("name"): str,
})


class DaikinAircleanerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_SCHEMA)

        for entry in self._async_current_entries():
            if entry.data.get(CONF_IP_ADDRESS) == user_input[CONF_IP_ADDRESS]:
                return self.async_abort(reason="already_configured")

        errors = {}
        for entry in self._async_current_entries():
            if entry.data.get("name") == user_input["name"] or entry.title == user_input["name"]:
                errors["name"] = "name_exists"
                break

        if errors:
            return self.async_show_form(step_id="user", data_schema=_SCHEMA, errors=errors)

        return self.async_create_entry(title=user_input["name"], data=user_input)
