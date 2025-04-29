import logging
from typing import Optional

from .const import (
    AcMode,
    AirQuality,
    ChildLock,
    FilterType,
    LightState,
    SwitchState,
    TimerEnum,
    WindSpeed,
)


class ProtocolHeader:
    """
    解析后存储 UDP 协议头信息的容器。
    """

    def __init__(
        self,
        ack_required: bool,
        unknown_flag: bool,
        wifi_locked: bool,
        mac_address: str,
        protocol_index: int,
        company_code: int,
        device_type: int,
        auth_code: int,
        content_length: int,
        payload: bytes,
    ):
        # 对应 Java 中 a.f7614a = (b[1] & 2) != 0
        self.ack_required = ack_required
        # 对应 Java 中 a.f7615b = (b[1] & 0) != 0  （始终 False）
        self.unknown_flag = unknown_flag
        # 对应 Java 中 a.f7617d = (b[1] & 4) != 0
        self.wifi_locked = wifi_locked

        # MAC 地址，格式 "AA:BB:CC:DD:EE:FF"
        self.mac_address = mac_address

        # 对应 Java 中 a.f7618e = protocol index
        self.protocol_index = protocol_index
        # 对应 Java 中 a.f7619f = companyCode
        self.company_code = company_code
        # 对应 Java 中 a.f7620g = deviceType
        self.device_type = device_type
        # 对应 Java 中 a.f7622i = authCode
        self.auth_code = auth_code

        # 对应 Java 中 a.f7623j = contentLength
        self.content_length = content_length
        # 对应 Java 中 a.f7624k = payload bytes
        self.payload = payload

    def __repr__(self):
        return (
            f"<ProtocolHeader mac={self.mac_address} ack_required={self.ack_required} "
            f"wifi_locked={self.wifi_locked} protocol_index={self.protocol_index} "
            f"company_code=0x{self.company_code:02X} device_type=0x{self.device_type:02X} "
            f"auth_code={self.auth_code} content_length={self.content_length} "
            f"payload={self.payload.hex()}>"
        )


def parse_protocol_header(data: bytes) -> Optional[ProtocolHeader]:
    """
    解析 UDP 包头，返回 ProtocolHeader 实例或 None（校验失败时）。
    对应 Java: C1636h.m7306a(byte[] bArr)
    """
    # 必须至少 16 字节
    if data is None or len(data) < 16:
        logging.warning("Packet header is incomplete.")
        return None

    # 第 0 字节必须是 0xA1（Java 中 -95）
    if data[0] != 0xA1:
        logging.warning("Wrong Protocol Version.")
        return None

    # 第 8 字节是 content length（unsigned）
    content_length = data[8]
    # Java 检查: if (i > bArr.length - 9)
    if content_length > len(data) - 9:
        logging.warning("Packet content is incomplete.")
        return None

    byte1 = data[1]
    ack_required = bool(byte1 & 0x02)
    unknown_flag = bool(
        byte1 & 0x01
    )  # 原代码里 &0，始终 False，我改成 &0x01 来保留“预留位”语义
    wifi_locked = bool(byte1 & 0x04)

    # MAC 地址 6 字节，转换成常见字符串
    mac_bytes = data[2:8]
    mac_address = ":".join(f"{b:02X}" for b in mac_bytes)

    # Protocol Index 两字节
    protocol_index = (data[10] << 8) | data[11]

    # Company Code / Device Type 各一字节
    company_code = data[12]
    device_type = data[13]

    # Auth Code 两字节
    auth_code = (data[14] << 8) | data[15]

    # 剩余就是 payload
    payload = data[16:] if len(data) > 16 else b""

    return ProtocolHeader(
        ack_required=ack_required,
        unknown_flag=unknown_flag,
        wifi_locked=wifi_locked,
        mac_address=mac_address,
        protocol_index=protocol_index,
        company_code=company_code,
        device_type=device_type,
        auth_code=auth_code,
        content_length=content_length,
        payload=payload,
    )


class DeviceState:
    """
    存放空调设备状态解析结果。
    """

    def __init__(
        self,
        ip: str,
        ac_mode: AcMode,
        filter_type: FilterType,
        wind_speed: WindSpeed,
        timer: TimerEnum,
        air_quality: AirQuality,
        child_lock: ChildLock,
        light_state: LightState,
        switch_state: SwitchState,
        last_timer: TimerEnum,
        pm: int,
        total_online_time: int,
        air_total_value: int,
        total_purification_value: int,
        linkage: int = 0,
    ):
        self.ac_mode = ac_mode
        self.filter_type = filter_type
        self.wind_speed = wind_speed
        self.timer = timer
        self.air_quality = air_quality
        self.child_lock = child_lock
        self.light_state = light_state
        self.switch_state = switch_state
        self.last_timer = last_timer
        self.pm = pm
        self.total_online_time = total_online_time
        self.air_total_value = air_total_value
        self.total_purification_value = total_purification_value
        self.linkage = linkage
        self.ip = ip

    def set_ip(self, ip: str):
        self.ip = ip

    def __repr__(self):
        return (
            f"<DeviceState ac_mode={self.ac_mode}"
            f" filter_type={self.filter_type}"
            f" wind_speed={self.wind_speed}"
            f" timer={self.timer}"
            f" air_quality={self.air_quality}"
            f" child_lock={self.child_lock}"
            f" light_state={self.light_state}"
            f" switch_state={self.switch_state}"
            f" last_timer={self.last_timer}"
            f" pm={self.pm}"
            f" total_online_time={self.total_online_time}"
            f" air_total_value={self.air_total_value}"
            f" total_purification_value={self.total_purification_value}"
            f" linkage={self.linkage}>"
        )


def parse_device_state_payload(data: bytes, device_ip: str) -> Optional[DeviceState]:
    """
    解析 33 字节的设备状态包，返回 DeviceState。
    对应 Java 里：
      if (bArr[1]==90 && bArr[2]==-95 && bArr.length==33) { … }
    """

    # 必要校验
    if len(data) != 33:
        return None
    if data[1] != 0x5A or data[2] != 0xA1:
        return None

    # --- byte 3: 低 4 位 = 模式(1-5)，高 4 位 = 滤网类型(0-2) ---
    b3 = data[3]
    ac_mode = AcMode(b3 & 0x0F)

    filter_type = FilterType((b3 & 0xF0) >> 4)

    # --- byte 4: 风速 (1-6) ---
    wind_speed = WindSpeed(data[4])

    # --- byte 5: 定时 (0-3,5,8) ---
    b5 = data[5]
    timer = TimerEnum(b5)

    # --- byte 6: 空气质量(1-3) ---
    air_quality = AirQuality(data[6])

    # --- byte 7: 童锁(0->0,17->1) ---
    child_lock = ChildLock(data[7])

    # --- byte 8: 灯光(0->1,17->0) ---
    light_state = LightState(data[8])

    # --- byte 9: 开关(0->1,17->0) ---
    switch_state = SwitchState(data[9])

    # --- bytes 10-11: 上次定时(大端) ---
    last_timer = TimerEnum((data[10] << 8) | data[11])

    # --- bytes 12-13: PM 值(大端) ---
    pm = (data[12] << 8) | data[13]

    # （原 Java 有条件更新 PM 到 Holder，这里不做任何写操作）

    # --- bytes 19-20: 在线时长(大端)，并做异常值过滤 ---
    tot_online = (data[19] << 8) | data[20]
    if tot_online > 65059 or (10000 < tot_online < 65000):
        tot_online = 0

    # --- bytes 21-23: 总空气量基数(22-23，大端)×倍率(21) ---
    base_air = (data[22] << 8) | data[23]
    mult_map = {0: 1, 1: 10, 2: 100, 3: 1000}
    air_total = base_air * mult_map.get(data[21], 1)

    # --- bytes 24-26: 净化量基数(25-26，大端)×倍率(24) ---
    base_purify = (data[25] << 8) | data[26]
    purify_total = base_purify * mult_map.get(data[24], 1)

    # --- byte 27: 联动状态 ---
    linkage = data[27]

    return DeviceState(
        ip=device_ip,
        ac_mode=ac_mode,
        filter_type=filter_type,
        wind_speed=wind_speed,
        timer=timer,
        air_quality=air_quality,
        child_lock=child_lock,
        light_state=light_state,
        switch_state=switch_state,
        last_timer=last_timer,
        pm=pm,
        total_online_time=tot_online,
        air_total_value=air_total,
        total_purification_value=purify_total,
        linkage=linkage,
    )


# —— 使用示例 ——
if __name__ == "__main__":
    # 一个合法的示例包（16 + 3 字节 payload）
    # raw = bytes.fromhex(
    #     # "a104009569da9fe028000012f1020605025aa1010300020000110000000000000000000000000000000000000000000000"
    #     "0xA1 0x04 0x00 0x95 0x69 0xDA 0x9F 0xE0 0x0E 0x00 0x00 0x1A 0xF1 0x02 0x06 0x05 0x01 0xA5 0xA0 0x5E 0x35 0x00 0xD8".replace(
    #         "0x", ""
    #     ).replace(
    #         " ", ""
    #     )
    # )
    # hdr = parse_protocol_header(raw)
    # print(hdr)
    # if not hdr:
    #     print("Failed to parse header")
    #     exit(1)

    import socket

    from .const import UDP_PORT

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow the socket to reuse the address
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to all interfaces and a specific port
    sock.bind(("", UDP_PORT))

    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received {len(data)} bytes from {addr}")
        hdr = parse_protocol_header(data)
        if hdr:
            print(hdr)
            payload = parse_device_state_payload(hdr.payload, addr[0])
            if payload:
                print(payload)
            else:
                print("Failed to parse payload")
        else:
            print("Failed to parse header")
