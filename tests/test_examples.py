from __future__ import annotations

from pathlib import Path

from alvorada.hashing import verify_hash_file
from alvorada.validator import validate_directory

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_valid_examples_acceptance() -> None:
    result = validate_directory(REPO_ROOT / "examples" / "valid")
    assert result["valid"] is True
    for path in sorted((REPO_ROOT / "examples" / "valid").glob("*.json")):
        assert verify_hash_file(path) is True


def test_invalid_examples_rejection() -> None:
    result = validate_directory(REPO_ROOT / "examples" / "invalid")
    assert result["valid"] is False
