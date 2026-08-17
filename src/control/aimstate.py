"""State machine for the autonomous aim loop.

The aim loop (``control/aim.py``) progresses through these states while
searching for and chasing the currently-targeted object:

- ``STOPPED``: no objective queued, no motion is published.
- ``SEARCHING``: objective queued but no detection in sight, slow rotation.
- ``AIMING``: object on screen but off-centre, rotate to face it.
- ``ADVANCING``: object centred (and not yet at stop-size), drive forward.
"""

from enum import IntEnum


class AimState(IntEnum):
    STOPPED = 0
    SEARCHING = 1
    AIMING = 3
    ADVANCING = 4
