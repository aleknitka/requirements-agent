"""Loguru sink configuration for the db package.

A stderr sink is installed once per process at the level taken from
``REQ_AGENT_LOG_LEVEL`` (default ``INFO``). File logs are per-project:
``add_project_log_sink(slug)`` installs a daily-rotated ``DEBUG`` sink
at ``projects/<slug>/logs/db-{YYYY-MM-DD}.log`` the first time it is
called for a given slug.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

_STDERR_CONFIGURED = False
_PROJECT_SINKS: dict[Path, int] = {}


def configure_logging() -> None:
    """Install the stderr loguru sink. Idempotent."""
    global _STDERR_CONFIGURED
    if _STDERR_CONFIGURED:
        return

    log_level = os.environ.get("REQ_AGENT_LOG_LEVEL", "INFO").upper()

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "<level>{level:<7}</level> "
            "<cyan>{name}</cyan> - <level>{message}</level>"
        ),
        enqueue=False,
    )

    _STDERR_CONFIGURED = True


def add_project_log_sink(project_dir: Path) -> None:
    """Install a daily-rotated DEBUG file sink at ``<project_dir>/logs/``.

    Idempotent per resolved directory.
    """
    project_dir = Path(project_dir).resolve()
    if project_dir in _PROJECT_SINKS:
        return

    log_dir = project_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    sink_id = logger.add(
        log_dir / "db-{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention=None,
        enqueue=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    )
    _PROJECT_SINKS[project_dir] = sink_id
