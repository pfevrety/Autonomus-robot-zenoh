from dataclasses import dataclass
from pycdr2 import IdlStruct
from pycdr2.types import int8, int32, uint32, float64

@dataclass
class Vector3(IdlStruct, typename="Vector3"):
    x: float64
    y: float64
    z: float64


@dataclass
class Twist(IdlStruct, typename="Twist"):
    linear: Vector3
    angular: Vector3


@dataclass
class Time(IdlStruct, typename="Time"):
    sec: int32
    nanosec: uint32


@dataclass
class Log(IdlStruct, typename="Log"):
    stamp: Time
    level: int8
    name: str
    msg: str
    file: str
    function: str
    line: uint32