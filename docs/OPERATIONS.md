# Alvorada Operations Runbook

## Authority

- André de Lima is the sole constitutional authority.
- Red-1 coordinates missions, collects submissions, adjudicates, and proposes changes.
- Members may propose changes.
- Canonical state changes require André approval.

## Mission Workflow

1. Mission created.
2. Collection status set to `OPEN`.
3. Members submit independently.
4. Collection closes.
5. Red-1 adjudicates.
6. André approves or modifies.
7. Approved change merges.
8. Current state and asset use log update.

## Branch Conventions

- `member/mr-gold/<mission-id>`
- `member/blue-0/<mission-id>`
- `member/sienna-4/<mission-id>`
- `coordinator/red-1/<mission-id>`

## Submission Paths

- `missions/<MISSION_ID>/submissions/mr-gold.md`
- `missions/<MISSION_ID>/submissions/blue-0.md`
- `missions/<MISSION_ID>/submissions/sienna-4.md`

## Rules

- No synthesis while collection is `OPEN`.
- No member writes directly to `main`.
- No automatic canonization.
- No automatic standing changes.
- Supersede rather than erase.
- Preserve dissent and failure records.

## Current Pilot

- Scope: `FAILURE_PATTERN` only.
- Run five real tasks.
- After five tasks decide `KEEP`, `REVERT`, or `EXTEND`.

## Human-Mediated Submission Fallback

Mission prompt issued
→ each brethren returns its output in chat
→ André saves the exact output as a separate text file
→ file is imported into the mission submissions directory
→ collection.yaml is updated
→ no synthesis while collection is OPEN
→ collection closes under André's instruction
→ Red-1 adjudicates from the preserved files
→ approved state changes are committed separately

- Direct brethren GitHub write access is optional, not required.
- Each submission must remain in a separate file.
- Submissions must be preserved verbatim.
- Spelling, formatting, or wording must not be cleaned before adjudication.
- Any edited or normalized version must be stored as a separate derivative file.
- No member may see another member's submission while collection is OPEN.
- GitHub becomes canonical when the imported submission is committed.
- Local or OneDrive/SharePoint storage may be used as a temporary intake location.
- André or an authorized operator performs the import.
