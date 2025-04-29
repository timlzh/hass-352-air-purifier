import aiohttp

from .const import AcMode, WindSpeed
from .device import AirPurifierDevice
from .model import LoginByPwdResponse
from .parser import parse_device_state_payload, parse_protocol_header
from .sign import SignUtil


class Air352API:
    EXT_BASE_URL = "https://352.yunext.com"
    token = None

    def __init__(self, phone: str, password: str):
        self.phone = phone
        self.password = password
        self.token = None

    async def login_by_pwd(self):
        url = f"{self.EXT_BASE_URL}/api2/user/loginByPwd"

        data = {
            "username": self.phone,
            "password": SignUtil.hash_md5(self.password),
            "appType": "2",
            "appVersion": "3.3.3",
        }
        data.update({"sign": SignUtil.sign_params(data)})

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                resp_raw = {}
                try:
                    resp_raw = await response.json()
                except ValueError:
                    pass

                login_resp = LoginByPwdResponse(resp_raw)
                if login_resp.ok:
                    self.token = login_resp.token
                else:
                    raise Exception(f"Login failed: {login_resp.msg}")
                return login_resp

    async def get_device_list(self) -> list[AirPurifierDevice]:
        url = f"{self.EXT_BASE_URL}/api2/device/getDeviceList"

        data = {
            "token": self.token,
        }
        data.update({"sign": SignUtil.sign_params(data)})

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                resp_raw = {}
                try:
                    resp_raw = await response.json()
                except ValueError:
                    pass

                devices = []

                if resp_raw.get("success", False):
                    for device in resp_raw.get("data", []):
                        devices.append(
                            AirPurifierDevice(
                                device["authCode"],
                                device["macAddress"],
                                device["deviceName"],
                                device["deviceType"],
                                device["companyCode"],
                            )
                        )

                return devices


if __name__ == "__main__":
    import asyncio

    class AirPurifierMessageHandler(asyncio.DatagramProtocol):
        """Protocol class for handling UDP responses from 352Air sensors."""

        def datagram_received(self, data, addr):
            """Receive incoming datagrams and parse them."""
            print(f"Received data: {data} from {addr}")
            hdr = parse_protocol_header(data)
            if hdr:
                state = parse_device_state_payload(hdr.payload, addr[0])
                print(f"Parsed payload: {state}")
            else:
                print("Failed to parse header")

    async def main():
        phone = "13696160525"
        password = "shiwoli123"
        api = Air352API(phone, password)
        try:
            login_response = await api.login_by_pwd()
            print("Login successful:", login_response)
            devices = await api.get_device_list()
            print("Devices:", devices)
            device = devices[0]
            await device.turn_on()
            await device.turn_light_off()
            await device.set_wind_speed(WindSpeed.ONE)
            await device.set_ac_mode(AcMode.SLEEP)

            async with device.send_and_handle(
                loop=asyncio.get_event_loop(),
                handler=lambda: AirPurifierMessageHandler(),
                data=device.build_read_device_state_command(),
            ):
                await asyncio.sleep(5)
        except Exception as e:
            print(e)

    asyncio.run(main())
