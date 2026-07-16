from __future__ import annotations

from pathlib import Path

from alvorada.hashing import hash_file, verify_hash_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_hash_round_trip() -> None:
    path = REPO_ROOT / "examples" / "valid" / "mission.json"
    assert len(hash_file(path)) == 64
    assert verify_hash_file(path) is True
