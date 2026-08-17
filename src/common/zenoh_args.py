"""Shared argparse + ``zenoh.Config`` bootstrap for CLI scripts.

Five scripts previously copy-pasted the same 30-line block of
``argparse`` + ``Config.from_file`` + ``insert_json5`` calls. This helper
collapses that pattern into one place.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Sequence

import zenoh


@dataclass
class ParsedZenohArgs:
    """Subset of CLI arguments actually consumed by the helpers below."""

    config: str | None
    mode: str | None
    connect: Sequence[str]
    listen: Sequence[str]
    prefix: str
    delay: float


def _build_parser(
    description: str,
    default_prefix: str,
    include_delay: bool,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["peer", "client"],
        help="Zenoh session mode.",
    )
    parser.add_argument(
        "-e",
        "--connect",
        action="append",
        metavar="ENDPOINT",
        help="Zenoh endpoint(s) to connect to.",
    )
    parser.add_argument(
        "-l",
        "--listen",
        action="append",
        metavar="ENDPOINT",
        help="Zenoh endpoint(s) to listen on.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default=default_prefix,
        help="Zenoh key-expression prefix.",
    )
    if include_delay:
        parser.add_argument(
            "-d",
            "--delay",
            type=float,
            default=0.05,
            help="Delay between iterations in seconds.",
        )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="FILE",
        help="Path to a Zenoh configuration file.",
    )
    return parser


def parse_zenoh_args(
    description: str,
    default_prefix: str,
    *,
    include_delay: bool = True,
    argv: Sequence[str] | None = None,
) -> tuple[argparse.Namespace, zenoh.Config, zenoh.Logger]:
    """Parse the standard CLI arguments and return a ready-to-use session config.

    Mirrors the contract of the original hand-rolled blocks: callers should
    follow up with ``zenoh.init_log_from_env_or("error")`` themselves if they
    need logging configuration beyond the default.
    """
    parser = _build_parser(description, default_prefix, include_delay)
    args = parser.parse_args(argv)

    conf = (
        zenoh.Config.from_file(args.config) if args.config else zenoh.Config()
    )
    if args.mode:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect:
        conf.insert_json5("connect/endpoints", json.dumps(args.connect))
    if args.listen:
        conf.insert_json5("listen/endpoints", json.dumps(args.listen))

    return args, conf, zenoh
