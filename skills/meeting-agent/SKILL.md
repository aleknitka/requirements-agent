---
name: meeting-agent
description: >
  Log meeting minutes, extract and track decisions, manage action items, and integrate meeting summaries into project status. Use this skill when the user wants to "log this meeting", "record meeting minutes", "we just had a call about X", "add a decision", "what decisions are open?", "mark action item as done", "integrate this into project status", or pastes a Teams/Slack/Zoom transcript and asks to log it.
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Meeting Agent Skill
 
Logs meetings from any source, extracts decisions linked to requirements,
tracks action items, and integrates summaries into project status.
 
## Commands
 
```bash
# Log
uv run meeting log [--project <slug>] \
  --title "..." --by "<agent/user>" \
  --source teams|slack|direct|email|zoom|in-person|other \
  [--source-url "..."] [--occurred-at "YYYY-MM-DD"] \
  [--attendees '["Alice","Bob"]'] \
  [--summary "..."] [--raw-notes "..."] \
  [--decisions '[{"title":"...","made_by":["Alice"],"status":"open","affects_reqs":["REQ-DATA-XXXX"]}]'] \
  [--action-items '[{"description":"...","owner":"Alice","due_date":"2025-04-10"}]']

# Read
uv run meeting list  [--project <slug>] [--unintegrated] [--since YYYY-MM-DD]
uv run meeting get   [--project <slug>] --id MTG-XXXXXXXX
uv run meeting decisions [--project <slug>] [--status open] [--affects-req REQ-XXXX]

# Update
uv run meeting update_decision [--project <slug>] \
  --meeting-id MTG-XXX --decision-id DEC-XXX --status actioned [--notes "..."]
uv run meeting close_action [--project <slug>] \
  --meeting-id MTG-XXX --action-id ACT-XXX

# Integrate into project status (also refreshes PROJECT.md)
uv run meeting integrate [--project <slug>] \
  --all-unintegrated \
  --status-summary "<updated project narrative>"
```
 
Decision statuses: open · actioned · superseded · deferred
