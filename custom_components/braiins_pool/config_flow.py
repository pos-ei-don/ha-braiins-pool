"""Config flow for the Braiins Pool integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE, CONF_API_TOKEN, DOMAIN, PROFILE_EP


class BraiinsPoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow: a single read-only API token."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the API token and validate it against the profile endpoint."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username, error = await self._validate(user_input[CONF_API_TOKEN])
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(username)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Braiins Pool ({username})",
                    data={CONF_API_TOKEN: user_input[CONF_API_TOKEN]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )

    async def _validate(self, token: str) -> tuple[str | None, str | None]:
        """Return (username, None) on success, else (None, error_key)."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{API_BASE}{PROFILE_EP}",
                headers={"Pool-Auth-Token": token},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    return None, "invalid_auth"
                if resp.status != 200:
                    return None, "cannot_connect"
                data = await resp.json()
                return data.get("username") or "account", None
        except aiohttp.ClientError:
            return None, "cannot_connect"
