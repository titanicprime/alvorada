from __future__ import annotations

import pytest

from alvorada.delta import apply_operations
from alvorada.exceptions import DeltaError
from alvorada.hashing import hash_data


def test_delta_replay_reconstructs_genesis_and_hash() -> None:
    base: dict[str, object] = {}
    first_value = {"status": "draft"}
    first_hash = hash_data(first_value, exclude_integrity=False)
    operations = [
        {
            "delta_id": "DELTA-1",
            "operation": "ADD",
            "target": "/task",
            "prior_hash": None,
            "resulting_value": first_value,
            "basis": {"reason": "Create task"},
            "claim_refs": ["CLM-1"],
            "timestamp": "2026-07-16T00:00:00Z",
        },
        {
            "delta_id": "DELTA-2",
            "operation": "SUPERSEDE",
            "target": "/task",
            "prior_hash": first_hash,
            "resulting_value": {"status": "done"},
            "basis": {"reason": "Complete task"},
            "claim_refs": ["CLM-2"],
            "timestamp": "2026-07-16T00:01:00Z",
        },
    ]
    result = apply_operations(base, operations)
    replay = apply_operations({}, operations)
    assert result["state"] == {"task": {"status": "done"}}
    assert replay["state_hash"] == result["state_hash"]
    assert result["lineage"][0]["superseded_value"] == first_value


def test_delta_replay_fails_on_missing_parent() -> None:
    with pytest.raises(DeltaError):
        apply_operations(
            {},
            [
                {
                    "delta_id": "DELTA-3",
                    "operation": "ADD",
                    "target": "/task/status",
                    "prior_hash": None,
                    "resulting_value": "new",
                    "basis": {"reason": "Missing parent"},
                    "claim_refs": [],
                    "timestamp": "2026-07-16T00:00:00Z",
                }
            ],
        )


def test_delta_replay_fails_on_mismatched_prior_hash() -> None:
    with pytest.raises(DeltaError):
        apply_operations(
            {"task": {"status": "draft"}},
            [
                {
                    "delta_id": "DELTA-4",
                    "operation": "MODIFY",
                    "target": "/task",
                    "prior_hash": "0" * 64,
                    "resulting_value": {"status": "done"},
                    "basis": {"reason": "Bad hash"},
                    "claim_refs": [],
                    "timestamp": "2026-07-16T00:00:00Z",
                }
            ],
        )
