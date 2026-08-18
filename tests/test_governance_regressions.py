from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from alvorada.governance import validate_governance

REPO_ROOT = Path(__file__).resolve().parents[1]


def authority(rule_id: str = "AUTH-HUMAN") -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "rule_type": "authority",
        "authority_basis": "FOUNDATIONAL",
        "foundational_basis": {
            "claim_type": "HUMAN_AUTHORITY_CLAIM",
            "evidence": ["evidence.md"],
            "provenance_status": "EVIDENCED",
        },
        "scope": [
            "adjudicate",
            "authorize",
            "certify",
            "create_mission",
            "execute",
            "coordinate",
        ],
        "holder": "HUMAN",
        "holder_type": "human",
        "status": "ACTIVE",
        "provenance": {"artifact": "evidence.md", "authorized_by": None, "status": "DOCUMENTED"},
    }


def delegation(rule_id: str = "DEL-COORDINATE") -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "rule_type": "delegation",
        "authority_source": "AUTH-HUMAN",
        "grantor": "HUMAN",
        "grantee": "COORDINATOR",
        "scope": ["coordinate"],
        "subdelegation": "PROHIBITED",
        "status": "ACTIVE",
        "expiry": None,
        "provenance": {"artifact": "grant.md", "authorized_by": "HUMAN"},
    }


def base_document() -> dict[str, Any]:
    return {
        "as_of": "2026-08-18T00:00:00Z",
        "external_authorities": ["EXTERNAL-HUMAN-SOURCE"],
        "authorities": [authority()],
        "delegations": [],
        "offices": [],
        "missions": [],
        "events": [],
        "rules": [],
        "claims": [],
        "human_texts": [],
    }


def codes(document: dict[str, Any], severity: str) -> set[str]:
    return {item["code"] for item in validate_governance(document)[severity]}


def test_authority_laundering() -> None:
    document = base_document()
    document["authorities"][0].update(
        {"authority_basis": "DERIVED", "authority_source": "POPULAR-SUCCESS"}
    )
    assert "UNDEFINED_AUTHORITY" in codes(document, "errors")


def test_competence_does_not_create_authority() -> None:
    document = base_document()
    document["missions"] = [{"mission_id": "M1", "authority_source": "COMPETENT-MODEL"}]
    assert "MISSION_WITHOUT_AUTHORITY" in codes(document, "errors")


def test_consensus_does_not_create_truth() -> None:
    document = base_document()
    document["claims"] = [{"rule_id": "C1", "prior_status": "UNKNOWN", "consensus": True}]
    assert "UNKNOWN_PROMOTED_WITHOUT_EVIDENCE" in codes(document, "warnings")


def test_unknown_preservation() -> None:
    document = base_document()
    document["claims"] = [{"rule_id": "C1", "status": "UNKNOWN"}]
    assert validate_governance(document)["valid"] is True
    assert not codes(document, "warnings")


def test_manufactured_consensus_does_not_supply_authority() -> None:
    document = base_document()
    document["authorities"].append(
        {
            **authority("AUTH-CONSENSUS"),
            "authority_basis": "DERIVED",
            "authority_source": "CONSENSUS",
            "consensus": True,
        }
    )
    assert "UNDEFINED_AUTHORITY" in codes(document, "errors")


def test_category_collapse() -> None:
    document = base_document()
    document["events"] = [
        {"subject": "R1", "event_type": "PROPOSAL", "actor": "A"},
        {"subject": "R1", "event_type": "AUTHORIZATION", "actor": "A"},
    ]
    assert "PROPOSAL_AUTHORIZATION_COLLAPSE" in codes(document, "warnings")


def test_role_portability() -> None:
    document = base_document()
    document["delegations"] = [delegation()]
    document["offices"] = [
        {
            "office_id": "COORDINATOR",
            "implementation": "MODEL-INSTANCE-7",
            "scope": ["coordinate"],
            "grant_ids": ["DEL-COORDINATE"],
        }
    ]
    assert validate_governance(document)["valid"] is True
    assert "ROLE_IMPLEMENTATION_COLLAPSE" not in codes(document, "warnings")


def test_artifact_substitution() -> None:
    document = base_document()
    document["authorities"][0].update(
        {"authority_basis": "DERIVED", "authority_source": "README-FILE"}
    )
    assert "UNDEFINED_AUTHORITY" in codes(document, "errors")


def test_output_provenance_inversion() -> None:
    document = base_document()
    document["authorities"][0].update(
        {"authority_basis": "DERIVED", "authority_source": "AUTH-HUMAN"}
    )
    assert "SELF_ATTESTED_AUTHORITY" in codes(document, "errors")


def test_duplicate_rule_identifiers_are_rejected() -> None:
    document = base_document()
    document["rules"] = [{"rule_id": "AUTH-HUMAN"}]
    assert "DUPLICATE_RULE_ID" in codes(document, "errors")


def test_mission_without_authority() -> None:
    document = base_document()
    document["missions"] = [{"mission_id": "M1", "authority_source": "MISSING"}]
    assert "MISSION_WITHOUT_AUTHORITY" in codes(document, "errors")


def test_recommendation_to_authorization_collapse() -> None:
    document = base_document()
    document["events"] = [
        {"subject": "R1", "event_type": "PROPOSAL", "actor": "RECOMMENDER"},
        {"subject": "R1", "event_type": "AUTHORIZATION", "actor": "RECOMMENDER"},
    ]
    assert "PROPOSAL_AUTHORIZATION_COLLAPSE" in codes(document, "warnings")


def test_artificial_intelligence_does_not_create_foundational_authority() -> None:
    document = base_document()
    historical = authority("AUTH-HISTORY")
    historical.update(
        {
            "holder_type": "artificial_intelligence",
        }
    )
    document["authorities"].append(historical)
    assert "INVALID_FOUNDATIONAL_AUTHORITY_CLAIM" in codes(document, "errors")


def test_self_certification() -> None:
    document = base_document()
    document["events"] = [
        {"subject": "R1", "event_type": "INSPECTION", "actor": "A"},
        {"subject": "R1", "event_type": "CERTIFICATION", "actor": "A"},
    ]
    assert "INSPECTION_CERTIFICATION_COLLAPSE" in codes(document, "warnings")


def test_role_self_identification() -> None:
    document = base_document()
    document["offices"] = [
        {"office_id": "RED-1", "implementation": "RED-1", "scope": [], "grant_ids": []}
    ]
    assert "ROLE_IMPLEMENTATION_COLLAPSE" in codes(document, "warnings")


def test_semantic_drift() -> None:
    document = base_document()
    document["rules"] = [
        {"rule_id": "R1", "term": "authority", "definition": "valid grant"},
        {"rule_id": "R2", "term": "authority", "definition": "effective power"},
    ]
    assert "CONFLICTING_DEFINITIONS" in codes(document, "warnings")


def test_delegation_is_not_transfer() -> None:
    document = base_document()
    expanded = delegation()
    expanded["scope"] = ["coordinate", "found_institution"]
    document["delegations"] = [expanded]
    assert "AUTHORITY_SCOPE_ENLARGEMENT" in codes(document, "errors")


def test_expired_authority() -> None:
    document = base_document()
    expired = delegation()
    expired["expiry"] = "2026-01-01T00:00:00Z"
    document["delegations"] = [expired]
    assert "EXPIRED_DELEGATION_ACTIVE" in codes(document, "errors")


def test_emergency_scope() -> None:
    document = base_document()
    emergency = delegation()
    emergency.update({"emergency": True, "scope": ["coordinate", "seize_control"]})
    document["delegations"] = [emergency]
    assert "EMERGENCY_SCOPE_EXCEEDED" in codes(document, "errors")


def test_reversibility() -> None:
    document = base_document()
    document["rules"] = [{"rule_id": "R1", "reversibility": {"formal": "REVERSIBLE"}}]
    assert "WEAK_REVERSIBILITY" in codes(document, "warnings")


def test_effective_power_versus_formal_authority() -> None:
    document = base_document()
    document["formal_authority"] = "HUMAN"
    document["effective_power"] = "AUTOMATION"
    assert "EXPERIMENTAL_EFFECTIVE_POWER_PLACEHOLDER" in codes(document, "informational")
    assert "FORMAL_EFFECTIVE_POWER_DIVERGENCE" not in codes(document, "warnings")


def test_human_control_plane_legibility() -> None:
    content = (REPO_ROOT / "human-control-plane" / "current-governance.md").read_text()
    assert "Who currently has Constitutional Authority?" in content
    assert "`UNKNOWN`" in content
    assert "independent authority source" in content


def test_three_letter_acronym_expansion() -> None:
    document = base_document()
    document["human_texts"] = [{"rule_id": "T1", "text": "The ABC controls this record."}]
    assert "UNEXPLAINED_THREE_LETTER_ACRONYM" in codes(document, "warnings")
    document["human_texts"][0]["expanded_acronyms"] = ["ABC"]
    assert "UNEXPLAINED_THREE_LETTER_ACRONYM" in codes(document, "warnings")
    document["human_texts"][0]["text"] = "Alpha Beta Council (ABC) controls this record."
    assert "UNEXPLAINED_THREE_LETTER_ACRONYM" not in codes(document, "warnings")
    document["human_texts"][0]["text"] += " ABC remains responsible."
    assert "UNEXPLAINED_THREE_LETTER_ACRONYM" in codes(document, "warnings")


def test_broken_provenance() -> None:
    document = base_document()
    del document["authorities"][0]["provenance"]
    assert "BROKEN_PROVENANCE" in codes(document, "errors")


def test_unauthorized_subdelegation() -> None:
    document = base_document()
    child = delegation("DEL-CHILD")
    child.update(
        {
            "authority_source": "DEL-COORDINATE",
            "grantor": "COORDINATOR",
            "grantee": "WORKER",
        }
    )
    document["delegations"] = [delegation(), child]
    assert "UNAUTHORIZED_SUBDELEGATION" in codes(document, "errors")


def test_delegation_cycle() -> None:
    document = base_document()
    first = delegation("D1")
    first.update({"grantor": "A", "grantee": "B"})
    second = delegation("D2")
    second.update({"grantor": "B", "grantee": "A"})
    third = delegation("D3")
    third.update({"grantor": "A", "grantee": "C"})
    document["delegations"] = [first, second, third]
    assert "DELEGATION_CYCLE" in codes(document, "errors")


def test_broken_lineage_and_silent_supersession() -> None:
    document = base_document()
    document["rules"] = [
        {"rule_id": "R2", "supersedes": ["R1"]},
        {"rule_id": "R3", "replaces": "R2"},
    ]
    assert {"BROKEN_LINEAGE", "SILENT_SUPERSESSION"} <= codes(document, "errors")


def consequential_event(
    event_type: str = "AUTHORIZATION", source: str = "AUTH-HUMAN"
) -> dict[str, Any]:
    return {
        "event_id": f"EVENT-{event_type}",
        "rule_id": f"EVENT-{event_type}",
        "event_type": event_type,
        "actor": "HUMAN",
        "subject": "R1",
        "authority_source": source,
        "scope": [],
        "provenance": {"artifact": "event.md", "authorized_by": "HUMAN"},
    }


def test_authorization_event_requires_authority() -> None:
    document = base_document()
    event = consequential_event(source="MISSING")
    document["events"] = [event]
    assert "EVENT_WITHOUT_AUTHORITY" in codes(document, "errors")
    event["authority_source"] = "AUTH-HUMAN"
    assert validate_governance(document)["valid"] is True


@pytest.mark.parametrize(
    "event_type", ["ADJUDICATION", "AUTHORIZATION", "EXECUTION", "CERTIFICATION"]
)
def test_consequential_event_authority_is_scoped(event_type: str) -> None:
    document = base_document()
    event = consequential_event(event_type)
    document["events"] = [event]
    assert validate_governance(document)["valid"] is True
    event["actor"] = "OTHER"
    assert "EVENT_ACTOR_NOT_ENTITLED" in codes(document, "errors")
    event["actor"] = "HUMAN"
    event["scope"] = ["outside_grant"]
    assert "EVENT_SCOPE_EXCEEDS_AUTHORITY" in codes(document, "errors")


@pytest.mark.parametrize(
    "mutation",
    [
        {"status": "INACTIVE"},
        {"expiry": "2026-01-01T00:00:00Z"},
    ],
)
def test_consequential_event_authority_must_be_current(mutation: dict[str, Any]) -> None:
    document = base_document()
    document["authorities"][0].update(mutation)
    document["events"] = [consequential_event()]
    assert "EVENT_WITHOUT_ACTIVE_AUTHORITY" in codes(document, "errors")


def test_consequential_event_requires_provenance() -> None:
    document = base_document()
    event = consequential_event()
    del event["provenance"]
    document["events"] = [event]
    assert "EVENT_BROKEN_PROVENANCE" in codes(document, "errors")


@pytest.mark.parametrize(
    ("mutation", "valid"),
    [
        ({}, True),
        ({"status": "INACTIVE"}, False),
        ({"expiry": "2026-01-01T00:00:00Z"}, False),
        ({"scope": ["coordinate"]}, False),
    ],
)
def test_mission_authority_must_be_current_and_scoped(
    mutation: dict[str, Any], valid: bool
) -> None:
    document = base_document()
    document["authorities"][0].update(mutation)
    document["missions"] = [{"mission_id": "M1", "authority_source": "AUTH-HUMAN"}]
    assert ("MISSION_WITHOUT_AUTHORITY" not in codes(document, "errors")) is valid


def test_foundational_and_derived_authority_are_distinct() -> None:
    document = base_document()
    document["authorities"][0]["provenance"] = {
        "artifact": None,
        "authorized_by": None,
        "status": "UNKNOWN",
    }
    assert validate_governance(document)["valid"] is True
    assert "FOUNDATIONAL_PROVENANCE_UNVERIFIED" in codes(document, "warnings")

    derived = authority("AUTH-DERIVED")
    derived.update(
        {
            "authority_basis": "DERIVED",
            "authority_source": "AUTH-HUMAN",
            "scope": ["authorize"],
            "holder": "DELEGATE",
            "provenance": {"artifact": "grant.md", "authorized_by": "HUMAN"},
        }
    )
    document["authorities"].append(derived)
    assert validate_governance(document)["valid"] is True
    derived["authority_source"] = "AUTH-DERIVED"
    assert "SELF_ATTESTED_AUTHORITY" in codes(document, "errors")


@pytest.mark.parametrize("collection", ["authorities", "delegations", "offices", "events", "rules"])
def test_lineage_is_checked_across_governance_objects(collection: str) -> None:
    document = base_document()
    if collection == "authorities":
        record = authority("AUTH-NEW")
    elif collection == "delegations":
        record = delegation("DEL-NEW")
    elif collection == "offices":
        record = {"office_id": "OFFICE-NEW", "scope": [], "grant_ids": []}
    elif collection == "events":
        record = {"event_id": "EVENT-NEW", "event_type": "PROPOSAL", "actor": "A", "subject": "R"}
    else:
        record = {"rule_id": "RULE-NEW"}
    record["dependencies"] = ["MISSING"]
    document[collection].append(record)
    assert "BROKEN_LINEAGE" in codes(document, "errors")


def test_cross_object_lineage_can_resolve() -> None:
    document = base_document()
    document["rules"] = [{"rule_id": "RULE-NEW", "dependencies": ["AUTH-HUMAN"]}]
    document["events"] = [
        {
            "event_id": "EVENT-NEW",
            "event_type": "PROPOSAL",
            "actor": "A",
            "subject": "RULE-NEW",
            "supersedes": ["RULE-NEW"],
        }
    ]
    assert "BROKEN_LINEAGE" not in codes(document, "errors")


def test_separation_preserves_multiple_actors_per_function() -> None:
    document = base_document()
    document["events"] = [
        {"subject": "R1", "event_type": "PROPOSAL", "actor": "RED-1"},
        {"subject": "R1", "event_type": "PROPOSAL", "actor": "SIENNA-5"},
        {"subject": "R1", "event_type": "AUTHORIZATION", "actor": "RED-1"},
    ]
    warnings = validate_governance(document)["warnings"]
    collapse = [item for item in warnings if item["code"] == "PROPOSAL_AUTHORIZATION_COLLAPSE"]
    assert len(collapse) == 1
    assert "RED-1" in collapse[0]["message"]
    assert "SIENNA-5" not in collapse[0]["message"]


def test_bounded_emergency_delegation() -> None:
    document = base_document()
    emergency = delegation()
    emergency.update(
        {
            "emergency": True,
            "trigger": "An externally established emergency basis.",
            "expiry": "2026-12-01T00:00:00Z",
            "review_path": ["HUMAN"],
            "termination_condition": "The external trigger ends.",
            "self_extension": "PROHIBITED",
            "amendable_fields": [],
        }
    )
    document["delegations"] = [emergency]
    assert validate_governance(document)["valid"] is True
    emergency["expiry"] = None
    assert "INCOMPLETE_EMERGENCY_DELEGATION" in codes(document, "errors")
    emergency["expiry"] = "2026-12-01T00:00:00Z"
    emergency["amendable_fields"] = ["scope"]
    assert "EMERGENCY_SELF_REDEFINITION" in codes(document, "errors")


def test_emergency_requires_active_upstream_authority() -> None:
    document = base_document()
    emergency = delegation()
    emergency.update(
        {
            "emergency": True,
            "trigger": "An externally established emergency basis.",
            "expiry": "2026-12-01T00:00:00Z",
            "review_path": ["HUMAN"],
            "termination_condition": "The external trigger ends.",
            "self_extension": "PROHIBITED",
        }
    )
    document["delegations"] = [emergency]
    document["authorities"][0]["status"] = "INACTIVE"
    assert "EMERGENCY_WITHOUT_ACTIVE_AUTHORITY" in codes(document, "errors")


def test_emergency_cannot_self_authorize_extension() -> None:
    document = base_document()
    emergency = delegation()
    emergency.update(
        {
            "emergency": True,
            "trigger": "An externally established emergency basis.",
            "expiry": "2026-12-01T00:00:00Z",
            "review_path": ["HUMAN"],
            "termination_condition": "The external trigger ends.",
            "self_extension": "SEPARATELY_AUTHORIZED",
            "extension_authority_source": "DEL-COORDINATE",
        }
    )
    document["delegations"] = [emergency]
    assert "UNAUTHORIZED_EMERGENCY_EXTENSION" in codes(document, "errors")


def test_institutional_reference_resolution_states() -> None:
    document = base_document()
    document["missions"] = [{"mission_id": "M1", "authority_source": "AUTH-HUMAN"}]
    document["institutional_state"] = {
        "authorities": [{"id": "AUTH-HUMAN", "resolution": "RESOLVED"}],
        "offices": [{"id": "OFFICE-EXTERNAL", "resolution": "EXTERNAL"}],
        "delegations": [{"id": "DEL-UNKNOWN", "resolution": "UNKNOWN"}],
        "active_missions": [{"id": "MISSING", "resolution": "UNRESOLVED"}],
    }
    assert "FALSELY_RESOLVED_REFERENCE" not in codes(document, "errors")
    document["institutional_state"]["active_missions"][0]["resolution"] = "RESOLVED"
    assert "FALSELY_RESOLVED_REFERENCE" in codes(document, "errors")


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("deprecated_terminology", "DEPRECATED_TERMINOLOGY"),
        ("historical_role_name", "HISTORICAL_ROLE_NAME"),
        ("migration_opportunity", "MIGRATION_OPPORTUNITY"),
    ],
)
def test_informational_migration_findings(field: str, code: str) -> None:
    document = base_document()
    document["rules"] = [{"rule_id": "R1", field: True}]
    assert code in codes(document, "informational")


def test_warnings_are_not_fatal() -> None:
    document = base_document()
    document["claims"] = [{"rule_id": "C1", "prior_status": "UNKNOWN"}]
    result = validate_governance(document)
    assert result["warnings"]
    assert result["valid"] is True


def test_authority_record_input_is_not_mutated() -> None:
    document = base_document()
    original = deepcopy(document)
    validate_governance(document)
    assert document == original
