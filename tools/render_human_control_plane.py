from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_PLANE = REPO_ROOT / "human-control-plane" / "current-governance.md"
REQUIRED_SECTIONS = (
    "Who currently has Constitutional Authority?",
    "What foundational powers currently exist?",
    "What offices exist, who occupies them, and what authority do they have?",
    "What delegations are active?",
    "What missions are active?",
    "What governance documents are currently authoritative?",
    "What is disputed?",
    "What is unknown or unresolved?",
    "What historical artifacts remain relied upon?",
    "What is reversible?",
    "What requires renewed human authorization?",
    "What changed recently?",
)
UNKNOWN_SECTION = "## What is unknown or unresolved?"
UNKNOWN_MARKER = "`UNKNOWN`"


def main() -> int:
    content = CONTROL_PLANE.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in content]
    if missing:
        print("Human control plane is missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    unknown_start = content.find(UNKNOWN_SECTION)
    unknown_end = content.find("\n## ", unknown_start + len(UNKNOWN_SECTION))
    unknown_content = content[unknown_start : unknown_end if unknown_end >= 0 else None]
    if UNKNOWN_MARKER not in unknown_content:
        print(
            "Human control plane must preserve insufficient evidence as UNKNOWN.",
            file=sys.stderr,
        )
        return 1
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
