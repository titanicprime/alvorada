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
