"""Shared helpers for the Autonomous Robot Zenoh pipeline.

Centralises:
- CDR types (``Vector3``, ``Twist``) shared by the control and motor stacks,
- the canonical Zenoh key-expressions used across the project,
- argparse + ``zenoh.Config`` bootstrap duplicated across CLI scripts,
- small ``publish_*`` helpers used by every control-side script.

Importing from this package requires the repo root (or ``src/``) to be on
``sys.path``. The web entry point (``website/app.py``) handles that with a
``sys.path.append``; CLI scripts rely on being launched from the repo root.
"""

from .types import Vector3, Twist, Time, Log  # noqa: F401
from .topics import (  # noqa: F401
    OBJ_DETECT_PREFIX,
    OBJ_DETECT_CAMS_PATTERN,
    OBJ_DETECT_OBJECTS_PATTERN,
    CMD_VEL,
    KLAXON,
    HEARTBEAT,
    ROBOT_AIMED,
    ROBOT_STATE,
    ROBOT_FOUND_OBJECT,
    ROBOT_CONFIG_LATENCY,
    ROBOT_CONFIG_SENSITIVITY,
    zenoh_prefix,
)
from .zenoh_args import parse_zenoh_args, ParsedZenohArgs  # noqa: F401
from .publish import publish_twist, publish_klaxon  # noqa: F401
