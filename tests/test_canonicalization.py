from __future__ import annotations

from pathlib import Path

from alvorada.canonicalize import canonicalize_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_canonicalization_excludes_integrity_and_sorts_keys() -> None:
    path = REPO_ROOT / "examples" / "valid" / "ack.json"
    canonical = canonicalize_file(path).decode("utf-8")
    assert "integrity" not in canonical
    assert canonical.startswith('{"claims"')
