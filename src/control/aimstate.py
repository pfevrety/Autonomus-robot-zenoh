from enum import IntEnum

class AimState(IntEnum):
        STOPPED = 0
        SEARCHING = 1
        LOCATED = 2
        AIMING = 3