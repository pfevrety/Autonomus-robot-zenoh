"""Shared publishers for control-side commands.

Both the keyboard teleop and the web teleop build the same ``Twist`` payload
and send it on the same topic; the only variation is the linear/angular scale.
Centralising the construction avoids drift between the two implementations.
"""

from __future__ import annotations

from .topics import CMD_VEL, KLAXON
from .types import Twist, Vector3

__all__ = ["publish_twist", "publish_klaxon"]


def publish_twist(
    session,
    linear: float,
    angular: float,
    *,
    topic: str = CMD_VEL,
) -> None:
    """Send a ``Twist`` command on ``topic`` (default: the robot's cmd_vel bus)."""
    twist = Twist(
        linear=Vector3(x=float(linear), y=0.0, z=0.0),
        angular=Vector3(x=0.0, y=0.0, z=float(angular)),
    )
    session.put(topic, twist.serialize())


def publish_klaxon(
    session,
    sound_id: int = 1,
    *,
    topic: str = KLAXON,
) -> None:
    """Publish a klaxon sound ID on ``topic`` (default: the robot's klaxon bus)."""
    session.put(topic, str(sound_id).encode("utf-8"))
