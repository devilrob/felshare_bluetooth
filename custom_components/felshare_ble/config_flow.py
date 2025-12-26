from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.helpers.selector import selector
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_ADDRESS, CONF_NAME

class FelshareBleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_bluetooth(self, discovery_info: bluetooth.BluetoothServiceInfoBleak) -> FlowResult:
        address = discovery_info.address
        name = discovery_info.name or "Felshare Diffuser"
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": name}
        return await self.async_step_user({"address": address, "name": name})

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME, address)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={CONF_ADDRESS: address, CONF_NAME: name},
            )

        # Pick from any discovered BLE devices, or paste address manually.
        options = []
        seen: set[str] = set()
        for info in bluetooth.async_discovered_service_info(self.hass):
            if not info.address or info.address in seen:
                continue
            seen.add(info.address)
            label = f"{info.name or 'Unknown'} ({info.address})"
            options.append({"value": info.address, "label": label})
        options.sort(key=lambda o: o["label"].lower())

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): selector(
                    {
                        "select": {
                            "options": options,
                            "mode": "dropdown",
                            "custom_value": True,
                        }
                    }
                ),
                vol.Optional(CONF_NAME, default="Felshare Diffuser (BLE)"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
