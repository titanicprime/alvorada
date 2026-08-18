from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schemas"


def load(name: str) -> dict[str, Any]:
    with (SCHEMA_DIR / name).open(encoding="utf-8") as stream:
        value: Any = json.load(stream)
    assert isinstance(value, dict)
    return value


def registry() -> Registry[Any]:
    result: Registry[Any] = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = load(path.name)
        if "$id" in schema:
            result = result.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return result


@pytest.mark.parametrize(
    ("schema_name", "record"),
    [
        (
            "authority.schema.json",
            {
                "rule_id": "AUTH-1",
                "rule_type": "authority",
                "authority_source": "HUMAN-SOURCE",
                "purpose": "Record an evidenced authority claim.",
                "scope": ["review"],
                "holder": "HUMAN",
                "holder_type": "human",
                "status": "PROPOSED",
                "human_explanation": "A proposal only.",
                "provenance": {"artifact": "source.md", "authorized_by": "HUMAN"},
            },
        ),
        (
            "delegation.schema.json",
            {
                "rule_id": "DEL-1",
                "rule_type": "delegation",
                "authority_source": "AUTH-1",
                "purpose": "Permit review.",
                "scope": ["review"],
                "grantor": "HUMAN",
                "grantee": "REVIEWER",
                "subdelegation": "PROHIBITED",
                "effective_date": None,
                "expiry": None,
                "status": "PROPOSED",
                "human_explanation": "A proposed bounded delegation.",
                "provenance": {"artifact": "source.md", "authorized_by": "HUMAN"},
            },
        ),
        (
            "office.schema.json",
            {
                "rule_id": "OFFICE-1",
                "rule_type": "office",
                "purpose": "Define a reviewer separately from an implementation.",
                "office_id": "REVIEWER",
                "scope": ["review"],
                "grant_ids": ["DEL-1"],
                "status": "PROPOSED",
                "human_explanation": "A proposed office.",
            },
        ),
        (
            "governance-event.schema.json",
            {
                "rule_id": "EVENT-1",
                "rule_type": "governance_event",
                "purpose": "Record an evidenced proposal.",
                "event_id": "EVENT-1",
                "event_type": "PROPOSAL",
                "actor": "AUTHOR",
                "subject": "RULE-1",
                "evidence": ["proposal.md"],
                "status": "PROPOSED",
                "human_explanation": "An example, not a claim that the event occurred.",
                "provenance": {"artifact": "proposal.md", "authorized_by": "AUTHOR"},
            },
        ),
        (
            "institutional-state.schema.json",
            {
                "state_id": "STATE-1",
                "as_of": "2026-08-18T00:00:00Z",
                "authorities": [],
                "offices": [],
                "delegations": [],
                "active_missions": [],
                "disputed": [],
                "unknown": ["Complete authority provenance"],
                "status": "UNKNOWN",
                "human_explanation": "Example state preserving an unknown.",
                "provenance": ["source.md"],
            },
        ),
    ],
)
def test_initial_governance_schema_accepts_human_readable_record(
    schema_name: str, record: dict[str, Any]
) -> None:
    validator = Draft202012Validator(load(schema_name), registry=registry())
    assert not list(validator.iter_errors(record))
