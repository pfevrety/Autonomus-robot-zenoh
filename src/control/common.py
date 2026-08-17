"""Backward-compatible re-export of CDR types from the shared package.

The historical layout had the dataclasses declared here. The canonical
home is now ``src/common/types.py``; this shim keeps the old import
paths (``from control.common import Vector3, Twist``) working so external
entry points that bootstrap ``sys.path`` against ``src/`` keep compiling.
"""

from common.types import Log, Time, Twist, Vector3

__all__ = ["Log", "Time", "Twist", "Vector3"]
