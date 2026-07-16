from __future__ import annotations

from pathlib import Path
from typing import Any

from alvorada.canonicalize import load_json_file
from alvorada.delta import apply_operations
from alvorada.exceptions import DeltaError, LineageError
from alvorada.hashing import hash_data


def verify_lineage_object(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise LineageError("Lineage verification expects a JSON object.")
    if "delta" in document and isinstance(document["delta"], dict):
        operations = document["delta"].get("operations", [])
        try:
            result = apply_operations({}, operations)
        except DeltaError as error:
            raise LineageError(str(error)) from error
        return {
            "valid": True,
            "lineage_count": len(result["lineage"]),
            "state_hash": result["state_hash"],
            "errors": [],
            "warnings": [],
        }
    if "lineage" in document:
        lineage = document["lineage"]
        if not isinstance(lineage, list):
            raise LineageError("lineage must be a list.")
        for entry in lineage:
            if (
                hash_data(entry["superseded_value"], exclude_integrity=False)
                != entry["superseded_hash"]
            ):
                raise LineageError("Lineage entry hash does not match preserved value.")
        return {"valid": True, "lineage_count": len(lineage), "errors": [], "warnings": []}
    raise LineageError("No lineage or delta information found.")


def verify_lineage_path(path: Path) -> dict[str, Any]:
    if path.is_dir():
        results = []
        for child in sorted(path.glob("*.json")):
            results.append({"path": str(child), **verify_lineage_object(load_json_file(child))})
        return {
            "valid": all(item["valid"] for item in results),
            "results": results,
            "errors": [],
            "warnings": [],
        }
    return verify_lineage_object(load_json_file(path))
