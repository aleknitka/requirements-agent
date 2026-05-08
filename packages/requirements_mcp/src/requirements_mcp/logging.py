"""Loguru configuration with stdout and daily-rotating file sinks.

The intended usage is to call :func:`configure_logging` once at process
start (CLI entry point, MCP server bootstrap, test fixture) and then use
``from loguru import logger`` everywhere else. Calling
:func:`configure_logging` again is safe: it removes existing handlers
before adding new ones, so handlers never accumulate when the function
is invoked from multiple entry points.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Union

from loguru import logger

__all__ = ["configure_logging", "logger"]

_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} - {message}"
)


def configure_logging(
    name: str = "requirements_mcp",
    log_dir: Union[Path, str] = "logs",
    level: str = "INFO",
    *,
    enable_stdout: bool = True,
    enable_file: bool = True,
):
    """Attach stdout and daily-rotating file sinks to the loguru logger.

    The file sink writes to ``<log_dir>/<name>-<YYYY-MM-DD>.log`` and
    rolls over at midnight. The current day's date is embedded in the
    filename via loguru's ``{time}`` placeholder, so each calendar day
    receives its own file and historical files are never overwritten.

    The function is idempotent: any handlers attached before the call are
    removed first. This means it is safe to invoke from a CLI entry
    point, from MCP server startup, and from per-test fixtures without
    producing duplicate log lines.

    Args:
        name: Filename prefix for the daily log file and a logical label
            shared by all messages emitted from this configuration.
        log_dir: Directory in which the daily log file is written. The
            directory and any missing parents are created if needed.
        level: Minimum severity emitted to both sinks. Accepts the usual
            loguru level names (``"TRACE"``, ``"DEBUG"``, ``"INFO"``,
            ``"WARNING"``, ``"ERROR"``, ``"CRITICAL"``).
        enable_stdout: When ``True``, attach a sink writing to
            ``sys.stdout`` so log lines are visible in the terminal and
            captured by container log collectors.
        enable_file: When ``True``, attach the daily-rotating file sink.
            Disable in tests or environments where on-disk logs are
            undesirable.

    Returns:
        The shared loguru ``logger`` instance, returned for convenience
        so callers may chain ``configure_logging(...).info("...")`` on a
        single line if they wish.
    """
    logger.remove()

    if enable_stdout:
        logger.add(sys.stdout, level=level, format=_FORMAT)

    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path / f"{name}-{{time:YYYY-MM-DD}}.log",
            level=level,
            format=_FORMAT,
            rotation="00:00",
            retention=None,
            encoding="utf-8",
        )

    return logger
