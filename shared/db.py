"""
CONSTANTS.py — single source of truth for all configuration.

PROJECTS_DIR defaults to a path relative to this file's location
(requirements-agent/projects/), so scripts work correctly regardless
of the working directory they are launched from.

To migrate to S3 later: replace PROJECTS_DIR with an S3-backed
path abstraction — no skill code needs to change.
"""

import os
import re
from pathlib import Path

# ── Storage ───────────────────────────────────────────────────────────────────

# Root of the agent repository — the directory containing shared/ and skills/
_AGENT_ROOT: Path = Path(__file__).resolve().parent.parent

# Root directory for all project subdirectories.
# Each project lives at: PROJECTS_DIR / <project-slug> /
#   <project-slug>.db
#   PROJECT.md
#
# Override with env var PROJECTS_DIR (absolute path only).
PROJECTS_DIR: Path = (
    Path(os.environ["PROJECTS_DIR"])
    if "PROJECTS_DIR" in os.environ
    else _AGENT_ROOT / "projects"
)

# ── Embedding ─────────────────────────────────────────────────────────────────

EMBEDDING_API_BASE: str = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")
EMBEDDING_API_KEY:  str = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL:    str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM:      int = int(os.getenv("EMBEDDING_DIM", "1536"))

# ── Update log policy ─────────────────────────────────────────────────────────

# Status values that trigger a full-row snapshot in the updates table.
SNAPSHOT_ON_STATUSES: set[str] = {"in-progress", "done", "rejected"}

# ── Project markdown ──────────────────────────────────────────────────────────

MD_NOTES_BEGIN: str = "<!-- NOTES:BEGIN -->"
MD_NOTES_END:   str = "<!-- NOTES:END -->"


# ── Path helpers ──────────────────────────────────────────────────────────────

def project_dir(slug: str) -> Path:
    """Return (and create) the directory for a given project slug."""
    p = PROJECTS_DIR / slug
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path(slug: str) -> Path:
    return project_dir(slug) / f"{slug}.db"


def md_path(slug: str) -> Path:
    return project_dir(slug) / "PROJECT.md"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
