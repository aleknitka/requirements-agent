---
name: meeting-agent
description: >
  Log meeting minutes, extract and track decisions, manage action items, and integrate meeting summaries into project status. Use this skill when the user wants to "log this meeting", "record meeting minutes", "we just had a call about X", "add a decision", "what decisions are open?", "mark action item as done", "integrate this into project status", or pastes a Teams/Slack/Zoom transcript and asks to log it.
license: MIT
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
python skills/meeting-agent/scripts/meeting.py log \
  --title "..." --by "<agent/user>" \
  --source teams|slack|direct|email|zoom|in-person|other \
  [--source-url "..."] [--occurred-at "YYYY-MM-DD"] \
  [--attendees '["Alice","Bob"]'] \
  [--summary "..."] [--raw-notes "..."] \
  [--decisions '[{"title":"...","made_by":["Alice"],"status":"open","affects_reqs":["REQ-DATA-XXXX"]}]'] \
  [--action-items '[{"description":"...","owner":"Alice","due_date":"2025-04-10"}]']
 
# Read
python skills/meeting-agent/scripts/meeting.py list  [--unintegrated] [--since YYYY-MM-DD]
python skills/meeting-agent/scripts/meeting.py get   --id MTG-XXXXXXXX
python skills/meeting-agent/scripts/meeting.py decisions [--status open] [--affects-req REQ-XXXX]
 
# Update
python skills/meeting-agent/scripts/meeting.py update_decision \
  --meeting-id MTG-XXX --decision-id DEC-XXX --status actioned [--notes "..."]
python skills/meeting-agent/scripts/meeting.py close_action \
  --meeting-id MTG-XXX --action-id ACT-XXX
 
# Integrate into project status (also refreshes PROJECT.md)
python skills/meeting-agent/scripts/meeting.py integrate \
  --all-unintegrated \
  --status-summary "<updated project narrative>"
```
 
Decision statuses: open · actioned · superseded · deferred