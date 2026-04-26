"""
md_writer.py — generates and maintains PROJECT.md for a project.

Structure
─────────
  # [AUTO] Header            regenerated on every refresh
  ## Stats                   live counts from DB
  ## Status                  latest status_summary
  ---
  <!-- NOTES:BEGIN -->
  ## Notes                   human/agent free-form — NEVER overwritten
  <!-- NOTES:END -->
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import CONSTANTS as C
from models import ProjectMeta


def regenerate(
    slug: str,
    meta: ProjectMeta,
    req_counts:    dict,
    status_counts: dict,
    open_decisions:       int,
    pending_actions:      int,
    unintegrated_meetings: int,
    fret_coverage: Optional[dict] = None,
) -> Path:
    path   = C.md_path(slug)
    notes  = _extract_notes(path)
    header = _build_header(meta, req_counts, status_counts,
                           open_decisions, pending_actions,
                           unintegrated_meetings, fret_coverage)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n" + _notes_block(notes), encoding="utf-8")
    return path


def append_note(slug: str, text: str) -> Path:
    path = C.md_path(slug)
    if not path.exists():
        raise FileNotFoundError(f"PROJECT.md not found: {path}")
    content = path.read_text(encoding="utf-8")
    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n### {ts}\n\n{text.strip()}\n"
    if C.MD_NOTES_BEGIN in content:
        content = content.replace(C.MD_NOTES_END, entry + "\n" + C.MD_NOTES_END)
    else:
        content += f"\n\n{C.MD_NOTES_BEGIN}\n{entry}\n{C.MD_NOTES_END}\n"
    path.write_text(content, encoding="utf-8")
    return path


def read_notes(slug: str) -> str:
    return _extract_notes(C.md_path(slug)) or ""


def _extract_notes(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    m = re.search(
        re.escape(C.MD_NOTES_BEGIN) + r"(.*?)" + re.escape(C.MD_NOTES_END),
        content, re.DOTALL,
    )
    if not m:
        return None
    raw = m.group(1).strip()
    # Strip leading "## Notes" heading captured inside the block
    if raw.startswith("## Notes"):
        raw = raw[len("## Notes"):].lstrip("\n")
    return raw


def _notes_block(existing: Optional[str]) -> str:
    inner = existing or "*Add free-form notes here. Never overwritten by auto-generation.*"
    return f"{C.MD_NOTES_BEGIN}\n## Notes\n\n{inner}\n{C.MD_NOTES_END}\n"


def _build_header(
    meta: ProjectMeta,
    req_counts: dict,
    status_counts: dict,
    open_decisions: int,
    pending_actions: int,
    unintegrated_meetings: int,
    fret_coverage: Optional[dict],
) -> str:
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {meta.name}",
        f"> *Auto-generated — last updated {now}*  ",
        "",
    ]
    if meta.code:          lines.append(f"**Code:** `{meta.code}`  ")
    lines.append(          f"**Phase:** {meta.phase.value}  ")
    if meta.project_owner: lines.append(f"**Owner:** {meta.project_owner}  ")
    if meta.sponsor:       lines.append(f"**Sponsor:** {meta.sponsor}  ")
    if meta.start_date:    lines.append(f"**Start:** {meta.start_date}  ")
    if meta.target_date:   lines.append(f"**Target:** {meta.target_date}  ")
    lines.append("")

    if meta.objective:
        lines += ["## Objective", "", meta.objective, ""]
    if meta.business_case:
        lines += ["## Business Case", "", meta.business_case, ""]
    if meta.success_criteria:
        lines += ["## Success Criteria", ""] + [f"- {c}" for c in meta.success_criteria] + [""]
    if meta.out_of_scope:
        lines += ["## Out of Scope", ""] + [f"- {o}" for o in meta.out_of_scope] + [""]
    if meta.stakeholders:
        lines += ["## Key Stakeholders", ""]
        for s in meta.stakeholders:
            c = f" — {s.contact}" if s.contact else ""
            lines.append(f"- **{s.name}** ({s.role}){c}")
        lines.append("")
    if meta.external_links:
        lines += ["## External Links", ""]
        for l in meta.external_links:
            u = f" — [{l.url}]({l.url})" if l.url else ""
            lines.append(f"- **{l.system}:** {l.label}{u}")
        lines.append("")

    total = sum(req_counts.values())
    lines += ["## Stats", "", f"**Requirements:** {total} total"]
    if req_counts:
        lines.append("- By type: " + ", ".join(f"{k}: {v}" for k, v in sorted(req_counts.items())))
    if status_counts:
        lines.append("- By status: " + ", ".join(f"{k}: {v}" for k, v in sorted(status_counts.items())))
    if fret_coverage:
        pct = fret_coverage.get("pct", 0)
        lines.append(f"- FRET coverage: {fret_coverage.get('with_fret',0)}/{total} ({pct:.0f}%)")
    lines += [
        "",
        f"**Open decisions:** {open_decisions}  ",
        f"**Pending actions:** {pending_actions}  ",
        f"**Meetings awaiting integration:** {unintegrated_meetings}  ",
        "",
    ]
    if meta.status_summary:
        ts = meta.status_updated_at.strftime("%Y-%m-%d") if meta.status_updated_at else ""
        lines += [f"## Project Status" + (f" *(as of {ts})*" if ts else ""),
                  "", meta.status_summary, ""]
    lines.append("---")
    return "\n".join(lines)
