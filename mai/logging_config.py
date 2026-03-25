"""One-time logging setup for the Mai process (level from ``LOG_LEVEL`` env)."""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False

_LEVEL_NAMES: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def configure_logging(level: str | int | None = None) -> None:
    """
    Configure the root logger once (idempotent).

    ``level``: override; otherwise ``LOG_LEVEL`` env (default ``INFO``).
    Discord library loggers are capped at WARNING to avoid HTTP noise.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    if isinstance(level, int):
        root_level = level
    else:
        raw = (level or os.getenv("LOG_LEVEL") or "INFO").strip().upper()
        root_level = _LEVEL_NAMES.get(raw, logging.INFO)

    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=root_level,
        format=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
    )
    root = logging.getLogger()
    root.setLevel(root_level)

    for name in ("discord", "discord.client", "discord.http", "discord.gateway"):
        logging.getLogger(name).setLevel(logging.WARNING)

    _CONFIGURED = True
