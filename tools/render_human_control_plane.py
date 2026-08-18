from __future__ import annotations

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


def main() -> int:
    content = CONTROL_PLANE.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in content]
    if missing:
        print("Human control plane is missing: " + ", ".join(missing))
        return 1
    if "`UNKNOWN`" not in content:
        print("Human control plane must preserve insufficient evidence as UNKNOWN.")
        return 1
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
