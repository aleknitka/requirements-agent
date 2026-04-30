"""
CONSTANTS.py — single source of truth for all configuration.

PROJECT_DIR defaults to a path relative to this file's location
(requirements-agent/project/), so scripts work correctly regardless
of the working directory they are launched from.

Override with env var PROJECT_DIR (absolute path only).
"""

import os
from pathlib import Path

# ── Storage ───────────────────────────────────────────────────────────────────

# Root of the agent repository — the directory containing src/ and skills/
_AGENT_ROOT: Path = Path(__file__).resolve().parents[2]

# Single project directory: project/ at the repo root.
# Structure: project/project.db, project/PROJECT.md, project/logs/, project/notes/
#
# Override with env var PROJECT_DIR (absolute path only).
# Raises ValueError if PROJECT_DIR is set to a non-absolute path to prevent
# relative path traversal (T-02-01).
_env_project_dir = os.environ.get("PROJECT_DIR")
if _env_project_dir is not None:
    _env_path = Path(_env_project_dir)
    if not _env_path.is_absolute():
        raise ValueError(
            f"PROJECT_DIR env var must be an absolute path, got: {_env_project_dir!r}"
        )
    PROJECT_DIR: Path = _env_path
else:
    PROJECT_DIR = _AGENT_ROOT / "project"

DB_PATH: Path = PROJECT_DIR / "project.db"
MD_PATH: Path = PROJECT_DIR / "PROJECT.md"

# ── Embedding ─────────────────────────────────────────────────────────────────

EMBEDDING_API_BASE: str = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")
EMBEDDING_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1536"))

# ── Update log policy ─────────────────────────────────────────────────────────

# Status values that trigger a full-row snapshot in the updates table.
SNAPSHOT_ON_STATUSES: set[str] = {"in-progress", "done", "rejected"}

# ── Project markdown ──────────────────────────────────────────────────────────

MD_NOTES_BEGIN: str = "<!-- NOTES:BEGIN -->"
MD_NOTES_END: str = "<!-- NOTES:END -->"
