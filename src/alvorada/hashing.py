from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from alvorada.canonicalize import canonicalize_data, load_json_file
from alvorada.exceptions import HashVerificationError


def hash_data(data: Any, *, exclude_integrity: bool = True) -> str:
    return hashlib.sha256(canonicalize_data(data, exclude_integrity=exclude_integrity)).hexdigest()


def hash_file(path: Path) -> str:
    return hash_data(load_json_file(path))


def verify_hash_data(data: Any) -> bool:
    expected = data.get("integrity", {}).get("sha256") if isinstance(data, dict) else None
    if not isinstance(expected, str):
        raise HashVerificationError("Missing integrity.sha256 field.")
    actual = hash_data(data)
    if actual != expected:
        raise HashVerificationError(f"Hash mismatch: expected {expected}, got {actual}.")
    return True


def verify_hash_file(path: Path) -> bool:
    return verify_hash_data(load_json_file(path))
