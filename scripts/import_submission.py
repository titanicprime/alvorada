"""Import a brethren text submission into a mission collection."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

MISSION_ID_PATTERN = re.compile(r"^ALVORADA_MISSION_\d+$")
ALLOWED_MEMBERS = ("MR_GOLD", "BLUE_0", "SIENNA_4")
MEMBER_TO_FILENAME = {
    "MR_GOLD": "mr-gold.txt",
    "BLUE_0": "blue-0.txt",
    "SIENNA_4": "sienna-4.txt",
}
OBVIOUS_CREDENTIAL_MARKERS = (
    "ghp_",
    "github_pat_",
    "BEGIN PRIVATE KEY",
    "Authorization:",
    "x-access-token",
)
REPO_ROOT = Path(__file__).resolve().parent.parent


class SubmissionImportError(Exception):
    """Raised when submission import cannot proceed."""


def validate_mission_id(mission_id: str) -> None:
    if not MISSION_ID_PATTERN.fullmatch(mission_id):
        raise SubmissionImportError("mission ID must match ALVORADA_MISSION_<number>")


def validate_member(member: str) -> None:
    if member not in ALLOWED_MEMBERS:
        allowed = ", ".join(ALLOWED_MEMBERS)
        raise SubmissionImportError(f"member must be one of: {allowed}")


def validate_iso8601(timestamp: str) -> None:
    normalized = timestamp.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SubmissionImportError("received-at must be a valid ISO-8601 timestamp") from exc


def load_collection(path: Path) -> dict:
    if not path.exists():
        raise SubmissionImportError(f"collection file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SubmissionImportError(f"collection file must be a YAML mapping: {path}")

    if data.get("status") != "OPEN":
        raise SubmissionImportError("collection is not OPEN")
    return data


def read_source_text(path: Path) -> str:
    if not path.exists():
        raise SubmissionImportError(f"source file not found: {path}")

    source = path.read_text(encoding="utf-8")
    if source.strip() == "":
        raise SubmissionImportError("source submission is empty")
    return source


def contains_obvious_credential_marker(source: str) -> str | None:
    lowered = source.lower()
    for marker in OBVIOUS_CREDENTIAL_MARKERS:
        if marker.lower() in lowered:
            return marker
    return None


def build_submission_text(
    mission_id: str,
    member: str,
    received_at: str,
    source_environment: str,
    imported_by: str,
    source: str,
) -> str:
    return (
        f"MISSION_ID: {mission_id}\n"
        f"MEMBER: {member}\n"
        f"RECEIVED_AT: {received_at}\n"
        f"SOURCE_ENVIRONMENT: {source_environment}\n"
        "STATUS: SUBMITTED_FOR_COLLECTION\n"
        "EDITED_AFTER_RECEIPT: NO\n"
        f"IMPORTED_BY: {imported_by}\n\n"
        "--- BEGIN VERBATIM SUBMISSION ---\n\n"
        f"{source}\n\n"
        "--- END VERBATIM SUBMISSION ---\n"
    )


def update_collection_members(collection: dict, member: str) -> None:
    received = collection.get("received", [])
    missing = collection.get("missing", [])

    if not isinstance(received, list):
        raise SubmissionImportError("collection received field must be a list")
    if not isinstance(missing, list):
        raise SubmissionImportError("collection missing field must be a list")

    if member not in received:
        received.append(member)
    collection["received"] = received
    collection["missing"] = [name for name in missing if name != member]


def import_submission(
    repo_root: Path,
    mission_id: str,
    member: str,
    source_file: Path,
    source_environment: str,
    received_at: str,
    imported_by: str,
) -> tuple[Path, dict]:
    validate_mission_id(mission_id)
    validate_member(member)
    validate_iso8601(received_at)

    mission_dir = repo_root / "missions" / mission_id
    if not mission_dir.exists():
        raise SubmissionImportError(f"mission directory not found: {mission_dir}")

    collection_path = mission_dir / "collection.yaml"
    collection = load_collection(collection_path)
    source_text = read_source_text(source_file)

    marker = contains_obvious_credential_marker(source_text)
    if marker is not None:
        raise SubmissionImportError(
            f"source submission contains obvious credential marker: {marker}"
        )

    target_path = mission_dir / "submissions" / MEMBER_TO_FILENAME[member]
    if target_path.exists():
        raise SubmissionImportError(f"canonical submission already exists: {target_path}")

    target_path.write_text(
        build_submission_text(
            mission_id=mission_id,
            member=member,
            received_at=received_at,
            source_environment=source_environment,
            imported_by=imported_by,
            source=source_text,
        ),
        encoding="utf-8",
    )

    update_collection_members(collection, member)
    collection["status"] = "OPEN"
    collection_path.write_text(
        yaml.safe_dump(collection, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return target_path, collection


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a brethren mission submission text file.")
    parser.add_argument(
        "--mission-id", required=True, help="Mission ID (ALVORADA_MISSION_<number>)"
    )
    parser.add_argument("--member", required=True, choices=ALLOWED_MEMBERS)
    parser.add_argument("--source-file", required=True, type=Path)
    parser.add_argument("--source-environment", required=True)
    parser.add_argument("--received-at", required=True, help="ISO-8601 timestamp")
    parser.add_argument("--imported-by", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        target_path, collection = import_submission(
            repo_root=REPO_ROOT,
            mission_id=args.mission_id,
            member=args.member,
            source_file=args.source_file,
            source_environment=args.source_environment,
            received_at=args.received_at,
            imported_by=args.imported_by,
        )
    except SubmissionImportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: filesystem operation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Imported file: {target_path}")
    print(f"Member: {args.member}")
    print(f"Received: {collection.get('received', [])}")
    print(f"Missing: {collection.get('missing', [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
