"""Create a new Alvorada mission scaffold and open collection state."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

MISSION_ID_PATTERN = re.compile(r"^ALVORADA_MISSION_\d+$")
EXPECTED_MEMBERS = ["MR_GOLD", "BLUE_0", "SIENNA_4"]
REPO_ROOT = Path(__file__).resolve().parent.parent


class MissionError(Exception):
    """Raised when mission creation cannot proceed."""


def validate_mission_id(mission_id: str) -> None:
    if not MISSION_ID_PATTERN.fullmatch(mission_id):
        raise MissionError("mission ID must match ALVORADA_MISSION_<number>")


def load_current_state(path: Path) -> dict:
    if not path.exists():
        raise MissionError(f"state file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MissionError(f"state file must contain a YAML mapping: {path}")
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def write_mission_markdown(path: Path, mission_id: str, title: str, question: str) -> None:
    text = f"# {mission_id}\n\n## Title\n\n{title}\n\n## Core Question\n\n> {question}\n"
    path.write_text(text, encoding="utf-8")


def create_collection_data() -> dict:
    return {
        "mission_id": None,
        "status": "OPEN",
        "expected": EXPECTED_MEMBERS.copy(),
        "received": [],
        "missing": EXPECTED_MEMBERS.copy(),
    }


def create_mission(repo_root: Path, mission_id: str, title: str, question: str) -> None:
    validate_mission_id(mission_id)

    mission_dir = repo_root / "missions" / mission_id
    if mission_dir.exists():
        raise MissionError(f"mission already exists: {mission_dir}")

    state_path = repo_root / "state" / "current.yaml"
    state = load_current_state(state_path)

    mission_file = mission_dir / "mission.md"
    collection_file = mission_dir / "collection.yaml"
    submissions_dir = mission_dir / "submissions"
    submissions_keep = submissions_dir / ".gitkeep"

    mission_dir.mkdir(parents=True, exist_ok=False)
    submissions_dir.mkdir(parents=False, exist_ok=False)

    write_mission_markdown(mission_file, mission_id, title, question)

    collection_data = create_collection_data()
    collection_data["mission_id"] = mission_id
    write_yaml(collection_file, collection_data)

    submissions_keep.touch(exist_ok=False)

    state["current_mission"] = mission_id
    state["collection_status"] = "OPEN"
    write_yaml(state_path, state)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new Alvorada mission scaffold.")
    parser.add_argument(
        "--mission-id", required=True, help="Mission ID (ALVORADA_MISSION_<number>)"
    )
    parser.add_argument("--title", required=True, help="Mission title")
    parser.add_argument("--question", required=True, help="Core mission question")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        create_mission(REPO_ROOT, args.mission_id, args.title, args.question)
    except MissionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: filesystem operation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created mission scaffold for {args.mission_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
