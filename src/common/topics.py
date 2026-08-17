"""Canonical Zenoh key-expressions for the Autonomous Robot pipeline.

Centralising the topics prevents the kind of drift that previously split
``robot/aimed`` from ``rt/turtle1/klaxon`` and made the klaxon sound ID a
mystery constant baked into the motor driver.
"""

from __future__ import annotations

# --- Detection pipeline (camera → YOLO → forwarder) -------------------------
OBJ_DETECT_PREFIX: str = "demo/obj-detect"
"""Prefix shared by camera frames and detected-object announcements."""

OBJ_DETECT_CAMS_PATTERN: str = f"{OBJ_DETECT_PREFIX}/cams/*"
"""Subscribe pattern: every JPEG frame published by every camera."""

OBJ_DETECT_OBJECTS_PATTERN: str = f"{OBJ_DETECT_PREFIX}/objects/*/*"
"""Subscribe pattern: every detection published by YOLO."""

# --- Robot command bus ------------------------------------------------------
CMD_VEL: str = "rt/turtle1/cmd_vel"
"""Velocity command consumed by ``motor/zdrive.py``."""

KLAXON: str = "rt/turtle1/klaxon"
"""Klaxon sound ID consumed by ``motor/zdrive.py``."""

HEARTBEAT: str = "rt/turtle1/heartbeat"
"""Heartbeat counter published by the motor driver."""

# --- High-level robot state (control ↔ web) ---------------------------------
ROBOT_AIMED: str = "robot/aimed"
"""Detection of the currently targeted object (only when one is selected)."""

ROBOT_STATE: str = "robot/state"
"""``True`` when the robot has at least one objective, ``False`` otherwise."""

ROBOT_FOUND_OBJECT: str = "robot/found_object"
"""Name of an object the robot has just reached."""

ROBOT_CONFIG_LATENCY: str = "robot/config/latency"
"""Aim loop latency, in milliseconds."""

ROBOT_CONFIG_SENSITIVITY: str = "robot/config/sensitivity"
"""Aim loop angular scale (degrees per step)."""


def zenoh_prefix(prefix: str, suffix: str) -> str:
    """Join ``prefix`` and ``suffix`` with a single ``/``.

    Tiny helper so the few call sites that need to compose key-expressions
    don't have to repeat the slash handling.
    """
    return f"{prefix.rstrip('/')}/{suffix.lstrip('/')}"
