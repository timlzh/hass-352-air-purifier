import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .air352.device import AirPurifierDevice
from .air352.parser import (
    parse_device_state_payload,
    parse_protocol_header,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AirPurifierMessageHandler(asyncio.DatagramProtocol):
    """Protocol class for handling UDP responses from 352Air sensors."""

    def __init__(self, coordinator: "AirPurifierCoordinator") -> None:
        self.coordinator = coordinator

    def datagram_received(self, data, addr):
        """Receive incoming datagrams and parse them."""
        print(f"Received data: {data} from {addr}")
        hdr = parse_protocol_header(data)
        if hdr:
            _LOGGER.debug(f"Parsed header: {hdr}")
            state = parse_device_state_payload(hdr.payload, addr[0])
            if state:
                _LOGGER.debug(f"Parsed payload: {state}")
                self.coordinator._device.state = state
                self.coordinator._updated = True
            else:
                _LOGGER.debug("Failed to parse payload")
        else:
            _LOGGER.debug("Failed to parse header")


class AirPurifierCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, device: AirPurifierDevice) -> None:
        self._hass = hass
        self._device = device
        self._updated = False
        self._max_retries = 3

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self):
        """Fetch data from the 352Air sensor."""
        for attempt in range(self._max_retries):
            try:
                return await self._async_get_device_state()
            except UpdateFailed as err:
                _LOGGER.error(f"Error updating device state: {err}")
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(1)
        raise UpdateFailed("Max retries reached while updating device state.")

    async def _async_get_device_state(self):
        """Get the state of the 352Air device."""
        try:
            self._updated = False
            async with self._device.send_and_handle(
                loop=self._hass.loop,
                handler=lambda: AirPurifierMessageHandler(self),
                data=self._device.build_read_device_state_command(),
            ):
                _LOGGER.debug("Waiting for data from 352Air sensor...")
                while not self._hass.is_stopping and not self._updated:
                    await asyncio.sleep(0.1)
        finally:
            if self._updated:
                _LOGGER.debug("Data received from 352Air sensor.")
                return self._device.state
            else:
                raise UpdateFailed("No data received from 352Air sensor.")
