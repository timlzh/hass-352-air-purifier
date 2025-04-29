import asyncio
import socket
from contextlib import asynccontextmanager
from typing import Callable

import async_timeout

from .const import AcMode, AcOnOff, LightState, SwitchState, WindSpeed
from .parser import DeviceState
from .sign import SignUtil


class AirPurifierDevice:
    authCode: str
    macAddress: str
    deviceName: str
    deviceType: str
    companyCode: str
    packageIndex: int = 0
    socket_lock: asyncio.Lock

    state: DeviceState | None = None

    def __init__(
        self,
        authCode: str,
        macAddress: str,
        deviceName: str,
        deviceType: str,
        companyCode: str,
        socket_lock: asyncio.Lock,
    ):
        self.authCode = authCode
        self.macAddress = macAddress
        self.deviceName = deviceName
        self.deviceType = deviceType
        self.companyCode = companyCode
        self.socket_lock = socket_lock

    def assemble_command(self, payload: bytes) -> bytes:
        result = bytearray()

        commandLen = len(payload) + 7
        result += bytes.fromhex("A104" + self.macAddress.replace(":", ""))
        result += bytearray(
            [
                commandLen & 0xFF,
                0,
                self.packageIndex >> 8,
                self.packageIndex & 0xFF,
            ]
        )
        result += bytes.fromhex(self.companyCode + self.deviceType + self.authCode)
        result += payload
        self.packageIndex += 1
        self.packageIndex &= 0xFFFF

        return bytes(result)

    def assemble_request_device_command(self, payload: bytes) -> bytes:
        deviceType = 0
        deviceCode = 0
        try:
            deviceType = int(self.deviceType)
        except ValueError:
            pass
        if deviceType == 1:
            deviceCode = 3
        elif 1 < deviceType <= 4:
            deviceCode = 1

        return self.assemble_command(bytearray([deviceCode]) + payload)

    def build_read_device_state_command(self):
        return self.assemble_request_device_command(bytearray([165, 160, 17, 17, 0, 0]))

    def build_ac_on_off(self, onOff: AcOnOff | None = None):
        if onOff is None:
            onOff = AcOnOff.ON
            if self.state:
                onOff = (
                    AcOnOff.OFF
                    if self.state.switch_state == SwitchState.ON
                    else AcOnOff.ON
                )
        return self.assemble_request_device_command(
            SignUtil.with_checksum(bytearray([165, 160, 94, onOff.value, 0]))
        )

    def build_light_on_off(self, onOff: LightState | None = None):
        if onOff is None:
            onOff = LightState.ON
            if self.state:
                onOff = (
                    LightState.OFF
                    if self.state.light_state == LightState.ON
                    else LightState.ON
                )
        return self.assemble_request_device_command(
            SignUtil.with_checksum(bytearray([165, 160, 86, onOff.value, 0]))
        )

    def build_wind_speed(self, windSpeed: WindSpeed):
        return self.assemble_request_device_command(
            SignUtil.with_checksum(bytearray([165, 160, 82, windSpeed.value, 0]))
        )

    def build_ac_mode(self, acMode: AcMode):
        return self.assemble_request_device_command(
            SignUtil.with_checksum(bytearray([165, 160, 81, acMode.value, 0]))
        )

    async def turn_on(self):
        await self.send(
            self.build_ac_on_off(AcOnOff.ON),
        )

    async def turn_off(self):
        await self.send(
            self.build_ac_on_off(AcOnOff.OFF),
        )

    async def turn_light_on(self):
        await self.send(
            self.build_light_on_off(LightState.ON),
        )

    async def turn_light_off(self):
        await self.send(
            self.build_light_on_off(LightState.OFF),
        )

    async def set_wind_speed(self, windSpeed: WindSpeed):
        await self.send(
            self.build_wind_speed(windSpeed),
        )

    async def set_ac_mode(self, acMode: AcMode):
        await self.send(
            self.build_ac_mode(acMode),
        )

    @asynccontextmanager
    async def send_and_handle(
        self,
        loop: asyncio.AbstractEventLoop,
        handler: Callable[[], asyncio.DatagramProtocol],
        data: bytes,
        srcAddr: tuple[str, int] = ("", 11530),
        destAddr: tuple[str, int] = ("255.255.255.255", 11530),
        timeout: int = 5,
    ):
        """Send a UDP message and handle the response."""
        async with self.socket_lock:
            transport = protocol = sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                sock.bind(srcAddr)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                transport, protocol = await loop.create_datagram_endpoint(
                    handler, sock=sock
                )
                transport.sendto(data, destAddr)

                async with async_timeout.timeout(timeout):
                    yield (transport, protocol)
            finally:
                if transport and protocol:
                    transport.close()
                if sock:
                    sock.close()

    @staticmethod
    async def send(
        data: bytes,
        srcAddr: tuple[str, int] = ("", 11530),
        destAddr: tuple[str, int] = ("255.255.255.255", 11530),
        timeout: int = 5,
    ):
        """Send a UDP message."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(timeout)
            sock.setblocking(False)
            sock.bind(srcAddr)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, destAddr)
            await asyncio.sleep(0.1)
        finally:
            sock.close()

    async def send_with_lock(self, data: bytes):
        """Send a UDP message with lock."""
        async with self.socket_lock:
            await self.send(data)
