"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.sensor import Entity, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.util import retry

import voluptuous as vol
import logging
from .pesic.wrapper import Client
from .const import DEFAULT_NAME, LOG_LEVEL

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(LOG_LEVEL)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    tries = 0
    max_tries = 6
    _LOGGER.debug(config)

    while tries < max_tries:
        try:
            with async_timeout.timeout(60*10):
                name = config[CONF_NAME]
                token = config[CONF_TOKEN]
                client = Client(token)
                add_entities([PesSensor(name, client)], update_before_add=True)

                platform = entity_platform.async_get_current_platform()
                platform.async_register_entity_service(
                    "indication_raw_updater",
                    {
                        vol.Required("peak_value"): cv.positive_int,
                        vol.Required("offpeak_value"): cv.positive_int,
                    },
                    "_send_raw_indication",
                )
                platform.async_register_entity_service(
                    "indication_incremental_updater",
                    {
                        vol.Required("peak_value"): cv.positive_int,
                        vol.Required("offpeak_value"): cv.positive_int,
                    },
                    "_send_incremental_indication",
                )
                return True
        except Exception as e:
            tries += 1
            if tries == max_tries:
                _LOGGER.error("Failed to set up custom component after %s tries", tries)
                return False
            _LOGGER.warning("Failed to set up custom component on try %s: %s", tries, e)

class PesSensor(Entity):
    def __init__(self, name: str, client: Client):
        super().__init__()
        self.client = client
        self._name = name
        self._attr_name = name
        self.attrs: Dict[str, Any] = {"account_id": None}
        self._available = False

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> Optional[str]:
        """Return balance as entity state"""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra attributes"""
        return self.attrs

    def update(self) -> None:
        _LOGGER.debug("Sensor update triggered")
        if not self.attrs["account_id"]:
            self.attrs["account_id"] = self.client.get_accounts()[0].get("accountId")
        data = self.client.get_account_data(self.attrs["account_id"])
        balance = data.get("balanceDetails").get("balance")
        for value in data.get("indicationInfo").get("subServices"):
            scale = value.get("scale").lower()
            self.attrs[scale + "_indication"] = value.get("value")
            self.attrs[scale + "_updated"] = value.get("date")
        self._attr_native_value = balance
        self.attrs["balance"] = balance
        self._state = balance
        self._available = True
        _LOGGER.debug(f"Update result: {data}")

    def _send_raw_indication(self, peak_value: int, offpeak_value: int):
        _LOGGER.debug(
            f"Send raw indication service has been triggered with peak {peak_value} and offpeak {offpeak_value} values."
        )
        result = self.client.update_meter_counters(
            [[peak_value, "DAY"], [offpeak_value, "NIGHT"]]
        )
        _LOGGER.debug("Result: " + str(result))
        self.update

    def _send_incremental_indication(self, peak_value: int, offpeak_value: int):
        _LOGGER.debug(
            f"Send incremental indication service has been triggered with peak {peak_value} and offpeak {offpeak_value} values."
        )
        total_peak = self.attrs["day_indication"] + peak_value
        total_offpeak = self.attrs["night_indication"] + offpeak_value
        result = self.client.update_meter_counters(
            [[int(total_peak), "DAY"], [int(total_offpeak), "NIGHT"]]
        )
        _LOGGER.debug("Result: " + str(result))
        self.update