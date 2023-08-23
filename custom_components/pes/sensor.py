"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.sensor import Entity, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD

import voluptuous as vol
import logging
from .pesic.wrapper import Client
from .const import DEFAULT_NAME, LOG_LEVEL, DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(LOG_LEVEL)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("peak_value"): cv.positive_int,
        vol.Required("offpeak_value"): cv.positive_int,
    }
)

SCAN_INTERVAL = timedelta(minutes=5)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    
    _LOGGER.debug(f"Setting up {DOMAIN} with {config}")

    name = config[CONF_NAME]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    client = Client(username=username, password=password)
    add_entities([PesSensor(name, client)], update_before_add=True)

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
        if data.get('errors'):
            _LOGGER.error(f"Error occured during sensor update. Details {data.get('errors')}")
        else:
            _LOGGER.debug(f"Update result: {data}")
            balance = data.get("balanceDetails").get("balance")
            for value in data.get("indicationInfo").get("subServices"):
                scale = value.get("scale").lower()
                self.attrs[scale + "_indication"] = value.get("value")
                self.attrs[scale + "_updated"] = value.get("date")
            self._attr_native_value = balance
            self.attrs["balance"] = balance
            self._state = balance
            self._available = True