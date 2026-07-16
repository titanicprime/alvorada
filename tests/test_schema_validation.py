from __future__ import annotations

from pathlib import Path

from alvorada.validator import validate_document

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_valid_examples_are_schema_valid() -> None:
    for path in sorted((REPO_ROOT / "examples" / "valid").glob("*.json")):
        result = validate_document(path)
        assert result["valid"], (path.name, result)


def test_invalid_examples_are_rejected() -> None:
    for path in sorted((REPO_ROOT / "examples" / "invalid").glob("*.json")):
        result = validate_document(path)
        assert not result["valid"], (path.name, result)
