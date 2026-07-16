from __future__ import annotations

from copy import deepcopy
from typing import Any

from alvorada.exceptions import DeltaError
from alvorada.hashing import hash_data


def _decode_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")


def _pointer_segments(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise DeltaError(f"Invalid target pointer: {pointer}")
    return [_decode_segment(part) for part in pointer.lstrip("/").split("/") if part]


def _get_parent(container: dict[str, Any], pointer: str) -> tuple[dict[str, Any], str]:
    segments = _pointer_segments(pointer)
    if not segments:
        raise DeltaError("Root replacement is not supported for delta operations.")
    node: dict[str, Any] = container
    for segment in segments[:-1]:
        next_node = node.get(segment)
        if not isinstance(next_node, dict):
            raise DeltaError(f"Missing parent state for target {pointer}")
        node = next_node
    return node, segments[-1]


def _get_value(container: dict[str, Any], pointer: str) -> tuple[bool, Any]:
    segments = _pointer_segments(pointer)
    if not segments:
        return True, container
    node: Any = container
    for segment in segments:
        if not isinstance(node, dict) or segment not in node:
            return False, None
        node = node[segment]
    return True, node


def apply_operations(
    base_state: dict[str, Any], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    state = deepcopy(base_state)
    lineage: list[dict[str, Any]] = []
    seen_delta_ids: set[str] = set()
    for operation in operations:
        delta_id = operation["delta_id"]
        if delta_id in seen_delta_ids:
            raise DeltaError(f"Duplicate delta_id: {delta_id}")
        seen_delta_ids.add(delta_id)
        pointer = operation["target"]
        exists, current_value = _get_value(state, pointer)
        prior_hash = operation["prior_hash"]
        if prior_hash is not None:
            if not exists:
                raise DeltaError(f"Missing target for prior_hash verification at {pointer}")
            actual_hash = hash_data(current_value, exclude_integrity=False)
            if actual_hash != prior_hash:
                raise DeltaError(
                    f"Mismatched prior hash for {pointer}: expected {prior_hash}, got {actual_hash}"
                )
        op = operation["operation"]
        if op == "VERIFY_UNCHANGED":
            if not exists:
                raise DeltaError(f"Cannot verify unchanged state for missing target {pointer}")
            continue
        parent, key = _get_parent(state, pointer)
        if op == "ADD":
            if key in parent:
                raise DeltaError(f"ADD operation target already exists: {pointer}")
            parent[key] = deepcopy(operation["resulting_value"])
        elif op == "MODIFY":
            if key not in parent:
                raise DeltaError(f"MODIFY operation target does not exist: {pointer}")
            parent[key] = deepcopy(operation["resulting_value"])
        elif op == "SUPERSEDE":
            if key not in parent:
                raise DeltaError(f"SUPERSEDE operation target does not exist: {pointer}")
            lineage.append(
                {
                    "delta_id": delta_id,
                    "target": pointer,
                    "timestamp": operation["timestamp"],
                    "operation": op,
                    "superseded_value": deepcopy(parent[key]),
                    "superseded_hash": hash_data(parent[key], exclude_integrity=False),
                }
            )
            parent[key] = deepcopy(operation["resulting_value"])
        elif op == "REJECT":
            if key not in parent:
                raise DeltaError(f"REJECT operation target does not exist: {pointer}")
            lineage.append(
                {
                    "delta_id": delta_id,
                    "target": pointer,
                    "timestamp": operation["timestamp"],
                    "operation": op,
                    "superseded_value": deepcopy(parent[key]),
                    "superseded_hash": hash_data(parent[key], exclude_integrity=False),
                }
            )
            del parent[key]
        else:
            raise DeltaError(f"Unsupported delta operation: {op}")
    return {
        "state": state,
        "lineage": lineage,
        "state_hash": hash_data(state, exclude_integrity=False),
    }
