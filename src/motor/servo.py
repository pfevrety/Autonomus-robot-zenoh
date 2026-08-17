"""Dynamixel XM430 protocol constants and thin serial wrapper.

The control tables are exposed as module-level constants (matching the
XM430-W350 datasheet) so that the rest of the codebase can reference them
without scattering magic numbers.
"""

from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler

# --- Control-table addresses (XM430-W350) -----------------------------------
MODEL_NUMBER = 0
MODEL_INFORMATION = 2
FIRMWARE_VERSION = 6
ID = 7
BAUD_RATE = 8

MILLIS = 10
MICROS = 14

DEVICE_STATUS = 18
HEARTBEAT = 19

EXTERNAL_LED_1 = 20
EXTERNAL_LED_2 = 21
EXTERNAL_LED_3 = 22
EXTERNAL_LED_4 = 23

BUTTON_1 = 26
BUTTON_2 = 27

BUMPER_1 = 28
BUMPER_2 = 29

ILLUMINATION = 30
IR = 34
SONAR = 38

BATTERY_VOLTAGE = 42
BATTERY_PERCENTAGE = 46

SOUND = 50

IMU_RE_CALIBRATION = 59

IMU_ANGULAR_VELOCITY_X = 60
IMU_ANGULAR_VELOCITY_Y = 64
IMU_ANGULAR_VELOCITY_Z = 68
IMU_LINEAR_ACCELERATION_X = 72
IMU_LINEAR_ACCELERATION_Y = 76
IMU_LINEAR_ACCELERATION_Z = 80
IMU_MAGNETIC_X = 84
IMU_MAGNETIC_Y = 88
IMU_MAGNETIC_Z = 92
IMU_ORIENTATION_W = 96
IMU_ORIENTATION_X = 100
IMU_ORIENTATION_Y = 104
IMU_ORIENTATION_Z = 108

PRESENT_CURRENT_LEFT = 120
PRESENT_CURRENT_RIGHT = 124
PRESENT_VELOCITY_LEFT = 128
PRESENT_VELOCITY_RIGHT = 132
PRESENT_POSITION_LEFT = 136
PRESENT_POSITION_RIGHT = 140

MOTOR_TORQUE_ENABLE = 149

CMD_VELOCITY_LINEAR_X = 150
CMD_VELOCITY_LINEAR_Y = 154
CMD_VELOCITY_LINEAR_Z = 158
CMD_VELOCITY_ANGULAR_X = 162
CMD_VELOCITY_ANGULAR_Y = 166
CMD_VELOCITY_ANGULAR_Z = 170

PROFILE_ACCELERATION_LEFT = 174
PROFILE_ACCELERATION_RIGHT = 178


class Servo:
    """Thin wrapper around ``dynamixel_sdk`` for a single XM430 servo."""

    def __init__(self, devicename: str, protocol_version: float, baudrate: int, dxl_id: int):
        self.id = dxl_id
        self.portHandler = PortHandler(devicename)
        self.packetHandler = PacketHandler(protocol_version)
        if not self.portHandler.openPort():
            raise RuntimeError(f"Failed to open serial port: {devicename}")
        if not self.portHandler.setBaudRate(baudrate):
            raise RuntimeError(f"Failed to set baudrate {baudrate} on {devicename}")

    def write1ByteTxRx(self, addr: int, val: int) -> None:
        dxl_comm_result, dxl_error = self.packetHandler.write1ByteTxRx(
            self.portHandler, self.id, addr, val
        )
        if dxl_comm_result != COMM_SUCCESS:
            print(self.packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print(self.packetHandler.getRxPacketError(dxl_error))

    def write2ByteTxRx(self, addr: int, val: int) -> None:
        dxl_comm_result, dxl_error = self.packetHandler.write2ByteTxRx(
            self.portHandler, self.id, addr, val
        )
        if dxl_comm_result != COMM_SUCCESS:
            print(self.packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print(self.packetHandler.getRxPacketError(dxl_error))

    def write4ByteTxRx(self, addr: int, val: int) -> None:
        dxl_comm_result, dxl_error = self.packetHandler.write4ByteTxRx(
            self.portHandler, self.id, addr, val
        )
        if dxl_comm_result != COMM_SUCCESS:
            print(self.packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print(self.packetHandler.getRxPacketError(dxl_error))
