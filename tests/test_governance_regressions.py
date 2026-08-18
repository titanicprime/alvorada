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
        "authority_source": "EXTERNAL-HUMAN-SOURCE",
        "scope": ["authorize", "create_mission", "coordinate"],
        "holder_type": "human",
        "status": "ACTIVE",
        "provenance": {"artifact": "evidence.md", "authorized_by": "HUMAN"},
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
    document["authorities"][0]["authority_source"] = "POPULAR-SUCCESS"
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
    document["authorities"][0]["authority_source"] = "README-FILE"
    assert "UNDEFINED_AUTHORITY" in codes(document, "errors")


def test_output_provenance_inversion() -> None:
    document = base_document()
    document["authorities"][0]["authority_source"] = "AUTH-HUMAN"
    assert "SELF_ATTESTED_AUTHORITY" in codes(document, "errors")


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


def test_historical_interpretation_does_not_create_foundational_authority() -> None:
    document = base_document()
    historical = authority("AUTH-HISTORY")
    historical.update(
        {
            "authority_source": "HISTORICAL-INTERPRETATION",
            "holder_type": "artificial_intelligence",
            "foundational": True,
        }
    )
    document["authorities"].append(historical)
    assert "ARTIFICIAL_FOUNDATIONAL_AUTHORITY" in codes(document, "errors")


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
    assert "FORMAL_EFFECTIVE_POWER_DIVERGENCE" in codes(document, "warnings")


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
    assert "UNEXPLAINED_THREE_LETTER_ACRONYM" not in codes(document, "warnings")


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
    document["delegations"] = [first, second]
    assert "DELEGATION_CYCLE" in codes(document, "errors")


def test_broken_lineage_and_silent_supersession() -> None:
    document = base_document()
    document["rules"] = [
        {"rule_id": "R2", "supersedes": ["R1"]},
        {"rule_id": "R3", "replaces": "R2"},
    ]
    assert {"BROKEN_LINEAGE", "SILENT_SUPERSESSION"} <= codes(document, "errors")


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
