"""The v2c component."""
from __future__ import annotations

from datetime import timedelta
import logging

from pytrydan import Trydan, TrydanData
from pytrydan.exceptions import TrydanError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


class V2CUpdateCoordinator(DataUpdateCoordinator[TrydanData]):
    """DataUpdateCoordinator to gather data from any v2c."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, evse: Trydan, host: str) -> None:
        """Initialize DataUpdateCoordinator for a v2c evse."""
        self.evse = evse
        super().__init__(
            hass,
            _LOGGER,
            name=f"EVSE {host}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> TrydanData:
        """Fetch sensor data from api."""
        try:
            data: TrydanData = await self.evse.get_data()
            _LOGGER.debug("Received data: %s", data)
            return data
        except TrydanError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
