from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import rfc8785


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_integrity(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: value for key, value in data.items() if key != "integrity"}
    return data


def canonicalize_data(data: Any, *, exclude_integrity: bool = True) -> bytes:
    candidate = strip_integrity(data) if exclude_integrity else data
    return rfc8785.dumps(candidate)


def canonicalize_file(path: Path, *, exclude_integrity: bool = True) -> bytes:
    return canonicalize_data(load_json_file(path), exclude_integrity=exclude_integrity)
