from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BleBoxSmartWindowBoxApi, BleBoxApiError
from .const import DOMAIN, CONF_HOST, CONF_NAME, DEFAULT_NAME


async def _validate(hass: HomeAssistant, host: str) -> dict:
    api = BleBoxSmartWindowBoxApi(async_get_clientsession(hass), host)
    info = await api.device_state()
    if not info.device_id:
        raise BleBoxApiError("No device id returned")
    return {
        "title": info.device_name or DEFAULT_NAME,
        "unique_id": info.device_id,
    }


class BleBoxSmartWindowBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            name = user_input.get(CONF_NAME) or None

            try:
                result = await _validate(self.hass, host)
            except BleBoxApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(result["unique_id"])
                self._abort_if_unique_id_configured()

                data = {CONF_HOST: host}
                if name:
                    data[CONF_NAME] = name

                return self.async_create_entry(
                    title=name or result["title"],
                    data=data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=""): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)