"""
meeting.py — log meeting minutes, extract decisions, link to requirements.

Commands
────────
  log             Log a meeting with summary, decisions, action items
  get             Fetch a full meeting record
  list            List meetings with filters
  decisions       List all decisions (cross-meeting)
  update_decision Update decision status
  close_action    Mark action item as done
  integrate       Mark meetings as integrated + write status summary
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import db
import project_session as ps
from models import ActionItem, Decision, DecisionStatus, MeetingSource, MinuteIn


def _ok(data):  print(json.dumps({"ok": True,  **data}, indent=2, default=str))
def _err(msg):  print(json.dumps({"ok": False, "error": msg}), file=sys.stderr); sys.exit(1)

def _pj(raw, label):
    if not raw: return []
    try:
        v = json.loads(raw)
        assert isinstance(v, list)
        return v
    except Exception:
        _err(f"--{label} must be a JSON array")

def _parse_dt(s):
    if not s: return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    _err(f"Cannot parse datetime '{s}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")


def cmd_log(args):
    slug, conn, _ = ps.resolve(args.project)
    minute_in = MinuteIn(
        title=args.title,
        source=MeetingSource(args.source) if args.source else MeetingSource.OTHER,
        source_url=args.source_url,
        occurred_at=_parse_dt(args.occurred_at) or datetime.now(timezone.utc),
        logged_by=args.by,
        attendees=_pj(args.attendees, "attendees") if args.attendees else [],
        summary=args.summary or "",
        raw_notes=args.raw_notes or "",
        decisions  =[Decision(**d)    for d in _pj(args.decisions,    "decisions")],
        action_items=[ActionItem(**a) for a in _pj(args.action_items, "action-items")],
    )
    row = db.insert_minute(conn, minute_in)
    ps.refresh_md(slug, conn)
    _ok({
        "meeting_id":       row.id,
        "title":            row.title,
        "decisions_logged": len(row.decisions),
        "actions_logged":   len(row.action_items),
        "decision_ids":     [d.decision_id for d in row.decisions],
        "action_ids":       [a.action_id   for a in row.action_items],
    })


def cmd_get(args):
    _, conn, _ = ps.resolve(args.project)
    row = db.get_minute(conn, args.id)
    if not row: _err(f"Meeting '{args.id}' not found.")
    _ok({"meeting": row.model_dump(mode="json")})


def cmd_list(args):
    _, conn, _ = ps.resolve(args.project)
    rows = db.list_minutes(conn,
                           source=args.source,
                           unintegrated=args.unintegrated,
                           since=args.since)
    _ok({
        "count": len(rows),
        "meetings": [
            {"meeting_id": m.id, "title": m.title, "source": m.source.value,
             "occurred_at": m.occurred_at.isoformat(), "attendees": m.attendees,
             "decisions": len(m.decisions), "action_items": len(m.action_items),
             "integrated": m.integrated_into_status,
             "summary_preview": m.summary[:200] + ("…" if len(m.summary) > 200 else "")}
            for m in rows
        ],
    })


def cmd_decisions(args):
    _, conn, _ = ps.resolve(args.project)
    decs = db.list_decisions(conn, status=args.status, affects_req=args.affects_req)
    _ok({"count": len(decs), "decisions": decs})


def cmd_update_decision(args):
    _, conn, _ = ps.resolve(args.project)
    row = db.get_minute(conn, args.meeting_id)
    if not row: _err(f"Meeting '{args.meeting_id}' not found.")
    updated = None
    for d in row.decisions:
        if d.decision_id == args.decision_id:
            d.status = DecisionStatus(args.status)
            if args.notes: d.notes = args.notes
            updated = d
            break
    if not updated: _err(f"Decision '{args.decision_id}' not found.")
    conn.execute(
        "UPDATE minutes SET decisions=? WHERE id=?",
        (json.dumps([d.model_dump(mode="json") for d in row.decisions], default=str),
         args.meeting_id)
    )
    conn.commit()
    _ok({"decision_id": updated.decision_id, "status": updated.status.value})


def cmd_close_action(args):
    _, conn, _ = ps.resolve(args.project)
    row = db.get_minute(conn, args.meeting_id)
    if not row: _err(f"Meeting '{args.meeting_id}' not found.")
    found = False
    for a in row.action_items:
        if a.action_id == args.action_id:
            a.done = True; found = True; break
    if not found: _err(f"Action '{args.action_id}' not found.")
    conn.execute(
        "UPDATE minutes SET action_items=? WHERE id=?",
        (json.dumps([a.model_dump(mode="json") for a in row.action_items], default=str),
         args.meeting_id)
    )
    conn.commit()
    _ok({"action_id": args.action_id, "done": True})


def cmd_integrate(args):
    slug, conn, meta = ps.resolve(args.project)
    marked = []
    if args.all_unintegrated:
        for m in db.list_minutes(conn, unintegrated=True):
            db.mark_integrated(conn, m.id)
            marked.append(m.id)
    elif args.meeting_ids:
        for mid in args.meeting_ids.split(","):
            mid = mid.strip()
            if not db.get_minute(conn, mid): _err(f"Meeting '{mid}' not found.")
            db.mark_integrated(conn, mid)
            marked.append(mid)

    if args.status_summary:
        meta.status_summary    = args.status_summary
        meta.status_updated_at = datetime.now(timezone.utc)
        db.upsert_project(conn, meta)

    ps.refresh_md(slug, conn)
    _ok({"integrated_meetings": marked,
         "status_summary_updated": bool(args.status_summary)})


def build_parser():
    p = argparse.ArgumentParser(description="Meeting agent")
    p.add_argument("--project", default=None)
    sub = p.add_subparsers(dest="command", required=True)
    SOURCES = [s.value for s in MeetingSource]
    DS      = [s.value for s in DecisionStatus]

    lg = sub.add_parser("log")
    lg.add_argument("--title",        required=True)
    lg.add_argument("--by",           required=True)
    lg.add_argument("--source",       choices=SOURCES, default="other")
    lg.add_argument("--source-url",   dest="source_url")
    lg.add_argument("--occurred-at",  dest="occurred_at")
    lg.add_argument("--attendees")
    lg.add_argument("--summary",      default="")
    lg.add_argument("--raw-notes",    dest="raw_notes", default="")
    lg.add_argument("--decisions",    default=None)
    lg.add_argument("--action-items", dest="action_items", default=None)

    gt = sub.add_parser("get");       gt.add_argument("--id", required=True)

    ls = sub.add_parser("list")
    ls.add_argument("--source",       choices=SOURCES)
    ls.add_argument("--unintegrated", action="store_true")
    ls.add_argument("--since")

    dc = sub.add_parser("decisions")
    dc.add_argument("--status",       choices=DS)
    dc.add_argument("--affects-req",  dest="affects_req")

    ud = sub.add_parser("update_decision")
    ud.add_argument("--meeting-id",   dest="meeting_id",  required=True)
    ud.add_argument("--decision-id",  dest="decision_id", required=True)
    ud.add_argument("--status",       choices=DS,         required=True)
    ud.add_argument("--notes",        default="")

    ca = sub.add_parser("close_action")
    ca.add_argument("--meeting-id",   dest="meeting_id",  required=True)
    ca.add_argument("--action-id",    dest="action_id",   required=True)

    ig = sub.add_parser("integrate")
    ig.add_argument("--meeting-ids",      dest="meeting_ids",      default=None)
    ig.add_argument("--all-unintegrated", dest="all_unintegrated", action="store_true")
    ig.add_argument("--status-summary",   dest="status_summary",   default=None)

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    {"log": cmd_log, "get": cmd_get, "list": cmd_list,
     "decisions": cmd_decisions, "update_decision": cmd_update_decision,
     "close_action": cmd_close_action, "integrate": cmd_integrate}[args.command](args)
