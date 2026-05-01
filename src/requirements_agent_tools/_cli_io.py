"""Shared CLI I/O helpers for the argparse-based skill CLIs.

All CLIs in this package emit a single JSON object on success (`{"ok": true, ...}`)
to stdout and a single JSON object on failure (`{"ok": false, "error": "..."}`)
to stderr with a non-zero exit code. These helpers centralize that contract so
each module does not redefine its own `_ok`/`_err`.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, NoReturn

import click
from tabulate import tabulate


def ok(data: dict | None = None, fmt: str = "json", **extra: Any) -> None:
    """Print payload to stdout as indented JSON or human-readable text."""
    payload: dict = {"ok": True}
    if data:
        payload.update(data)
    payload.update(extra)

    if fmt == "json":
        print(json.dumps(payload, indent=2, default=str))
        return

    # ── Human-readable formatting ──
    # Check for lists
    for key in ["requirements", "issues", "updates", "actions", "projects", "results"]:
        if key in payload and isinstance(payload[key], list):
            items = payload[key]
            if not items:
                click.secho(f"No {key} found.", fg="yellow")
                return
            click.secho(f"\n{key.upper()} ({len(items)})", fg="cyan", bold=True)
            click.echo(tabulate(items, headers="keys", tablefmt="simple"))
            return

    # Check for single entities
    for key in ["requirement", "issue", "project", "action", "report"]:
        if key in payload and isinstance(payload[key], (dict, list)):
            data = payload[key]
            if isinstance(data, dict):
                click.secho(
                    f"\n{key.upper()}: {data.get('id', data.get('project_id', ''))}",
                    fg="cyan",
                    bold=True,
                )
                main_fields = {
                    k: v for k, v in data.items() if not isinstance(v, (list, dict))
                }
                click.echo(tabulate(main_fields.items(), tablefmt="plain"))

                for k, v in data.items():
                    if isinstance(v, list) and v:
                        click.secho(f"\n{k.upper()}:", fg="blue", bold=True)
                        if all(isinstance(i, dict) for i in v):
                            click.echo(tabulate(v, headers="keys", tablefmt="simple"))
                        else:
                            for i in v:
                                click.echo(f" - {i}")
            else:
                # List of items directly under the key
                click.secho(f"\n{key.upper()} LIST", fg="cyan", bold=True)
                click.echo(tabulate(data, headers="keys", tablefmt="simple"))
            return

    # Default fallback
    print(json.dumps(payload, indent=2, default=str))


def err(msg: str, code: int = 1) -> NoReturn:
    """Print `{"ok": false, "error": msg}` to stderr and exit with `code`."""
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(code)


def parse_json_arg(raw: str | None, label: str) -> list:
    """Parse a CLI argument expected to be a JSON array. Empty/None → `[]`."""
    if not raw:
        return []
    try:
        v = json.loads(raw)
    except json.JSONDecodeError:
        err(f"--{label} must be a valid JSON array")
    if not isinstance(v, list):
        err(f"--{label} must be a valid JSON array")
    return v


_DT_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def parse_dt(s: str | None) -> datetime | None:
    """Parse a CLI datetime arg as UTC. Empty/None → `None`."""
    if not s:
        return None
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    err(f"Cannot parse datetime '{s}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
