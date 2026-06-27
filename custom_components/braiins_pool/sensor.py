"""Sensor platform for the Braiins Pool integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, GH_TO_TH
from .coordinator import BraiinsPoolCoordinator

UNIT_TH = "TH/s"
UNIT_BTC = "BTC"


def _ghs_to_ths(value: Any) -> float | None:
    """Convert Braiins' Gh/s to TH/s."""
    if value is None:
        return None
    try:
        return round(float(value) / GH_TO_TH, 2)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class AccountSensorDescription(SensorEntityDescription):
    """Account-level sensor with a value extractor over the profile dict."""

    value_fn: Callable[[dict[str, Any]], Any]


ACCOUNT_SENSORS: tuple[AccountSensorDescription, ...] = (
    AccountSensorDescription(
        key="hashrate_5m",
        name="Hashrate 5m",
        native_unit_of_measurement=UNIT_TH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:pickaxe",
        value_fn=lambda p: _ghs_to_ths(p.get("hash_rate_5m")),
    ),
    AccountSensorDescription(
        key="hashrate_60m",
        name="Hashrate 60m",
        native_unit_of_measurement=UNIT_TH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:pickaxe",
        value_fn=lambda p: _ghs_to_ths(p.get("hash_rate_60m")),
    ),
    AccountSensorDescription(
        key="hashrate_24h",
        name="Hashrate 24h",
        native_unit_of_measurement=UNIT_TH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:pickaxe",
        value_fn=lambda p: _ghs_to_ths(p.get("hash_rate_24h")),
    ),
    AccountSensorDescription(
        key="balance",
        name="Balance",
        native_unit_of_measurement=UNIT_BTC,
        suggested_display_precision=8,
        icon="mdi:currency-btc",
        value_fn=lambda p: p.get("current_balance"),
    ),
    AccountSensorDescription(
        key="today_reward",
        name="Today reward",
        native_unit_of_measurement=UNIT_BTC,
        # Resets daily; total_increasing lets HA treat the midnight reset as a
        # new cycle and still build long-term statistics.
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=8,
        icon="mdi:currency-btc",
        value_fn=lambda p: p.get("today_reward"),
    ),
    AccountSensorDescription(
        key="all_time_reward",
        name="All-time reward",
        native_unit_of_measurement=UNIT_BTC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=8,
        icon="mdi:currency-btc",
        value_fn=lambda p: p.get("all_time_reward"),
    ),
    AccountSensorDescription(
        key="ok_workers",
        name="Workers OK",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:server-network",
        value_fn=lambda p: p.get("ok_workers"),
    ),
)

# (key, label, unit, api_field, is_hashrate)
WORKER_SENSORS: tuple[tuple[str, str, str | None, str, bool], ...] = (
    ("hashrate_5m", "5m hashrate", UNIT_TH, "hash_rate_5m", True),
    ("hashrate_24h", "24h hashrate", UNIT_TH, "hash_rate_24h", True),
    ("state", "State", None, "state", False),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Braiins Pool sensors from a config entry."""
    coordinator: BraiinsPoolCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        BraiinsAccountSensor(coordinator, entry, desc) for desc in ACCOUNT_SENSORS
    ]
    # Workers present on first refresh. (Dynamic add/remove of workers over time
    # is a deliberate follow-up — see the ideas ticket.)
    for worker in coordinator.data.get("workers", {}):
        if worker.endswith("[auto]"):
            # Braiins' auto-scaling pseudo-worker, not a real device — skip it.
            continue
        for key, label, unit, field, is_hr in WORKER_SENSORS:
            entities.append(
                BraiinsWorkerSensor(
                    coordinator, entry, worker, key, label, unit, field, is_hr
                )
            )

    async_add_entities(entities)


class _BraiinsBaseSensor(CoordinatorEntity[BraiinsPoolCoordinator], SensorEntity):
    """Shared base: one device per account."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BraiinsPoolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def _username(self) -> str:
        return self.coordinator.data.get("username") or "account"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Braiins Pool ({self._username})",
            manufacturer="Braiins",
            configuration_url="https://pool.braiins.com/",
        )


class BraiinsAccountSensor(_BraiinsBaseSensor):
    """Account-level sensor."""

    entity_description: AccountSensorDescription

    def __init__(
        self,
        coordinator: BraiinsPoolCoordinator,
        entry: ConfigEntry,
        description: AccountSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_account_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data.get("profile", {}))


class BraiinsWorkerSensor(_BraiinsBaseSensor):
    """Per-worker sensor."""

    def __init__(
        self,
        coordinator: BraiinsPoolCoordinator,
        entry: ConfigEntry,
        worker: str,
        key: str,
        label: str,
        unit: str | None,
        field: str,
        is_hashrate: bool,
    ) -> None:
        super().__init__(coordinator, entry)
        self._worker = worker
        self._field = field
        self._is_hashrate = is_hashrate
        short = worker.split(".", 1)[-1]  # "pos_ei_don.hydro1" -> "hydro1"
        self._attr_name = f"{short} {label}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_worker_{worker}_{key}"
        if is_hashrate:
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_suggested_display_precision = 2
            self._attr_icon = "mdi:pickaxe"

    @property
    def _worker_data(self) -> dict[str, Any]:
        return self.coordinator.data.get("workers", {}).get(self._worker, {})

    @property
    def available(self) -> bool:
        return super().available and self._worker in self.coordinator.data.get(
            "workers", {}
        )

    @property
    def native_value(self) -> Any:
        value = self._worker_data.get(self._field)
        return _ghs_to_ths(value) if self._is_hashrate else value
