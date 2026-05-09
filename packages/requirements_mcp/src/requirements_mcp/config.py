"""Configuration helpers — database path, host, and port resolution.

Three runtime knobs are sourced through this module:

* the SQLite database path (:func:`resolve_db_path`),
* the bind host (:func:`resolve_host`),
* the bind port (:func:`resolve_port`).

The bind host and bind port follow the same four-step priority:

1. an explicit CLI argument (e.g. ``--port``);
2. the matching environment variable
   (``REQUIREMENTS_HOST`` / ``REQUIREMENTS_PORT``);
3. the value from ``config/default.yaml`` if it sets that key;
4. a built-in fallback.

The database path follows a shorter chain — CLI argument >
``REQUIREMENTS_DB_PATH`` env var > built-in default — and does **not**
read the YAML file. The expectation is that each checkout points at its
own database via env var or CLI flag, while ``host`` / ``port`` are the
knobs that need to differ between concurrent instances on one machine.

The YAML file is opt-in: if it is missing, malformed, unreadable, or
simply does not declare the key, the resolver falls back to the next
priority source with a warning — startup never crashes for a config-file
problem alone. The YAML is searched relative to the current working
directory under ``./config/default.yaml``; this matches how the project
is intended to be launched (from the repository root).

Multiple instances on the same machine are supported by giving each
its own port — set it once in ``config/default.yaml`` per checkout, or
pass ``--port`` / ``REQUIREMENTS_PORT`` per invocation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

DEFAULT_DB_PATH = Path("data") / "requirements.db"
"""Fixed SQLite location used by every command.

The path is *not* configurable. CLI flags and the
:data:`ENV_VAR` environment variable do not override it; the project
intentionally pins itself to a single database file under ``./data``
to keep onboarding and the ``--demo-data`` initialiser unambiguous.
"""

ENV_VAR = "REQUIREMENTS_DB_PATH"
"""Documented name of the historical override environment variable.

Retained as a module-level constant for backwards compatibility and as
documentation. Setting this variable has **no** runtime effect — see
:data:`DEFAULT_DB_PATH`.
"""

DEFAULT_CONFIG_PATH = Path("config") / "default.yaml"
"""Project-relative path to the YAML config file."""

DEFAULT_HOST = "127.0.0.1"
"""Built-in fallback bind address (loopback only)."""

DEFAULT_PORT = 7860
"""Built-in fallback HTTP port."""

HOST_ENV_VAR = "REQUIREMENTS_HOST"
"""Environment variable that overrides the YAML / built-in host."""

PORT_ENV_VAR = "REQUIREMENTS_PORT"
"""Environment variable that overrides the YAML / built-in port."""

_MIN_PORT = 1
_MAX_PORT = 65535


def resolve_db_path() -> Path:
    """Return the fixed absolute path of the project's SQLite database.

    The database path is locked to :data:`DEFAULT_DB_PATH` so every
    command — ``requirements-db-init``, ``requirements-mcp-server``, the
    Gradio frontend, and the MCP tools — operates on the same file. The
    path is expanded (``~``) and resolved to absolute form; the file
    itself does not need to exist.

    Returns:
        An absolute :class:`pathlib.Path` for ``data/requirements.db``.
    """
    return DEFAULT_DB_PATH.expanduser().resolve()


def load_yaml_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load ``config/default.yaml`` if present and return its contents.

    Args:
        path: Optional explicit file location. Defaults to
            ``./config/default.yaml`` relative to the current working
            directory.

    Returns:
        The parsed mapping, or an empty dict when the file does not
        exist or is not a YAML mapping at the top level. Logs a warning
        when the file exists but parses to a non-mapping (e.g. a list)
        so the misconfiguration is visible without aborting startup.
    """
    target = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not target.is_file():
        return {}
    try:
        with target.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (yaml.YAMLError, OSError) as exc:
        logger.warning(
            "Could not read or parse {} ({}); ignoring config file.", target, exc
        )
        return {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.warning(
            "{} did not parse to a mapping ({}); ignoring config file.",
            target,
            type(data).__name__,
        )
        return {}
    return data


def resolve_host(
    cli_arg: str | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> str:
    """Choose the bind host from CLI, environment, config file, and default.

    Priority order: ``cli_arg`` > ``REQUIREMENTS_HOST`` env var >
    ``host`` key from the YAML config > :data:`DEFAULT_HOST`.

    Args:
        cli_arg: Optional host supplied on the command line.
        config: Optional preloaded config mapping. When ``None``, the
            YAML file is loaded on demand.

    Returns:
        The resolved bind address as a string.
    """
    if cli_arg:
        return cli_arg
    env_value = os.environ.get(HOST_ENV_VAR)
    if env_value:
        return env_value
    cfg = load_yaml_config() if config is None else config
    raw = cfg.get("host")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return DEFAULT_HOST


def resolve_port(
    cli_arg: int | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> int:
    """Choose the bind port from CLI, environment, config file, and default.

    Priority order: ``cli_arg`` > ``REQUIREMENTS_PORT`` env var >
    ``port`` key from the YAML config > :data:`DEFAULT_PORT`.

    The selected value is validated against the legal TCP-port range
    [1, 65535]. An invalid environment variable or YAML entry is logged
    and ignored in favour of the next-priority source so a typo in the
    config file does not block startup.

    Args:
        cli_arg: Optional port supplied on the command line. ``argparse``
            will already have validated this is an int.
        config: Optional preloaded config mapping. When ``None``, the
            YAML file is loaded on demand.

    Returns:
        The resolved port as an int.

    Raises:
        ValueError: If ``cli_arg`` is supplied but out of range.
    """
    if cli_arg is not None:
        if not _MIN_PORT <= cli_arg <= _MAX_PORT:
            raise ValueError(
                f"--port {cli_arg} out of range; expected {_MIN_PORT}-{_MAX_PORT}"
            )
        return cli_arg
    env_value = os.environ.get(PORT_ENV_VAR)
    if env_value:
        try:
            parsed = int(env_value)
        except ValueError:
            logger.warning(
                "{}={!r} is not an integer; ignoring.", PORT_ENV_VAR, env_value
            )
        else:
            if _MIN_PORT <= parsed <= _MAX_PORT:
                return parsed
            logger.warning(
                "{}={} out of range [{}, {}]; ignoring.",
                PORT_ENV_VAR,
                parsed,
                _MIN_PORT,
                _MAX_PORT,
            )
    cfg = load_yaml_config() if config is None else config
    raw = cfg.get("port")
    if isinstance(raw, int) and not isinstance(raw, bool):
        if _MIN_PORT <= raw <= _MAX_PORT:
            return raw
        logger.warning(
            "config port {} out of range [{}, {}]; ignoring.",
            raw,
            _MIN_PORT,
            _MAX_PORT,
        )
    elif raw is not None:
        logger.warning(
            "config port {!r} is not an integer; ignoring.",
            raw,
        )
    return DEFAULT_PORT


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_DB_PATH",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ENV_VAR",
    "HOST_ENV_VAR",
    "PORT_ENV_VAR",
    "load_yaml_config",
    "resolve_db_path",
    "resolve_host",
    "resolve_port",
]
