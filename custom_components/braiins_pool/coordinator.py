"""DataUpdateCoordinator for the Braiins Pool integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    CONF_API_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROFILE_EP,
    WORKERS_EP,
)

_LOGGER = logging.getLogger(__name__)


class BraiinsPoolCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch account + worker stats from the Braiins Pool API (read-only)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._token: str = entry.data[CONF_API_TOKEN]
        self._session = async_get_clientsession(hass)

    async def _get(self, endpoint: str) -> dict[str, Any]:
        """GET a JSON endpoint with the auth-token header."""
        try:
            async with self._session.get(
                f"{API_BASE}{endpoint}",
                headers={"Pool-Auth-Token": self._token},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    raise ConfigEntryAuthFailed("Invalid Braiins Pool API token")
                if resp.status != 200:
                    raise UpdateFailed(f"{endpoint} returned HTTP {resp.status}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error talking to Braiins Pool: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll profile + workers."""
        profile = await self._get(PROFILE_EP)
        workers = await self._get(WORKERS_EP)
        return {
            "username": profile.get("username"),
            "profile": profile.get("btc", {}),
            "workers": workers.get("btc", {}).get("workers", {}),
        }
