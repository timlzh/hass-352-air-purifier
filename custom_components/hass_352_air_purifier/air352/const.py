from enum import Enum

UDP_PORT = 11530


class AcOnOff(Enum):
    ON = 53
    OFF = 17


class AcMode(Enum):
    AUTO = 1
    SLEEP = 2
    FAST = 3
    CUSTOM = 4
    RESERVED = 5


class FilterType(Enum):
    UNKNOWN = 0
    FILTER = 1
    RESERVED = 2


class WindSpeed(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class TimerEnum(Enum):
    NO_TIMER = 0
    ONE_HOUR = 1
    TWO_HOURS = 2
    THREE_HOURS = 3
    FIVE_HOURS = 5
    EIGHT_HOURS = 8


class AirQuality(Enum):
    GOOD = 1
    NORMAL = 2
    BAD = 3


class ChildLock(Enum):
    UNLOCK = 0
    LOCK = 17


class LightState(Enum):
    OFF = 17
    ON = 0


class SwitchState(Enum):
    ON = 0
    OFF = 17
