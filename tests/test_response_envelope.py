from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from alvorada.response_envelope import (
    load_identity_registry,
    render_response,
    validate_response_envelope,
    validate_response_text,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MR_GOLD_ROLE = "Formal Systems, Consistency, and Recursive-Control Analyst"
BLUE_0_ROLE = "Generalization and Outside-View Analyst"


def response() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "response_id": "RSP-TEST-001",
        "in_response_to": "ALV-CONFORM-001",
        "member_designation": "Mr. Gold",
        "canonical_role": MR_GOLD_ROLE,
        "message_type": "ANALYSIS",
        "authority_basis": {
            "reference": "ALV-CONFORM-001",
            "status": "DOCUMENTED",
        },
        "permitted_output_class": "REVIEW",
        "state_effect": "NONE",
        "content": {
            "formal_analysis": ["Identity and syntax are protocol coordinates."],
            "unresolved": ["Substantive correctness requires review."],
        },
    }


def codes(result: dict[str, Any], severity: str = "errors") -> set[str]:
    return {str(item["code"]) for item in result[severity]}


def test_correct_identity_and_role_specific_content_conform() -> None:
    result = validate_response_envelope(response())
    assert result["conformant"] is True
    assert result["identity"] == "MATCH"


def test_json_whitespace_does_not_change_conformance() -> None:
    document = response()
    text = json.dumps(document, indent=7, separators=(", ", " : "))
    parsed, result = validate_response_text(f"\n\n{text}\n")
    assert parsed == document
    assert result["conformant"] is True


def test_optional_extensions_may_be_omitted() -> None:
    document = response()
    assert "extensions" not in document
    assert validate_response_envelope(document)["conformant"] is True


def test_registered_extension_namespace_is_permitted() -> None:
    document = response()
    document["extensions"] = {"x_mr_gold_falsification": ["Counterexample"]}
    assert validate_response_envelope(document)["conformant"] is True


def test_valid_bounded_identity_correction() -> None:
    original = response()
    original["member_designation"] = "CONFORMANCE_EXAMINER_01"
    correction = {
        "schema_version": "1.0",
        "response_id": "RSP-TEST-002",
        "supersedes": original["response_id"],
        "member_designation": "Mr. Gold",
        "canonical_role": MR_GOLD_ROLE,
        "message_type": "CORRECTION",
        "correction": "IDENTITY_PROVENANCE_CORRECTED",
        "substantive_content_changed": "NO",
        "state_effect": "NONE",
    }
    result = validate_response_envelope(
        correction,
        response_index={str(original["response_id"]): original},
    )
    assert result["conformant"] is True
    assert result["identity"] == "MATCH"


def test_valid_examination_profile() -> None:
    document = response()
    document["message_type"] = "EXAMINATION"
    document["profile"] = "CONFORMANCE_EXAMINATION"
    document["content"] = {
        "scenarios": [
            {
                "scenario_id": "SCENARIO-1",
                "known": ["The response has a registered identity."],
                "unknown_or_unresolved": ["Substantive correctness."],
                "authority_analysis": {"finding": "No new authority is created."},
                "permitted": ["Review"],
                "prohibited": ["Self-authorization"],
                "state_effect": "NONE",
                "process_required": ["Human review"],
                "governing_principles": ["Conformance is not correctness."],
                "confidence": "HIGH",
            }
        ],
        "cross_scenario_conflicts": [],
        "constitutional_gaps_discovered": [],
        "self_assessed_conformance": "CONFORMANT",
    }
    assert validate_response_envelope(document)["conformant"] is True


def test_generic_examiner_is_not_mr_gold() -> None:
    document = response()
    document["member_designation"] = "CONFORMANCE_EXAMINER_01"
    result = validate_response_envelope(document)
    assert result["identity"] == "UNKNOWN_MEMBER"
    assert "UNKNOWN_MEMBER" in codes(result)


def test_noncanonical_member_spelling_is_identity_mismatch() -> None:
    document = response()
    document["member_designation"] = "MR_GOLD"
    result = validate_response_envelope(document)
    assert result["identity"] == "MISMATCH"
    assert "IDENTITY_MISMATCH" in codes(result)


def test_member_cannot_invent_canonical_role() -> None:
    document = response()
    document["canonical_role"] = "Conformance Examiner"
    result = validate_response_envelope(document)
    assert result["identity"] == "UNKNOWN_ROLE"
    assert "SELF_CREATED_ROLE" in codes(result)


def test_blue_zero_cannot_use_mr_gold_role() -> None:
    document = response()
    document["member_designation"] = "Blue-0"
    result = validate_response_envelope(document)
    assert result["identity"] == "MISMATCH"
    assert "ROLE_MISMATCH" in codes(result)


def test_missing_member_designation_fails() -> None:
    document = response()
    del document["member_designation"]
    result = validate_response_envelope(document)
    assert "IDENTITY_MISSING" in codes(result)


def test_duplicate_conflicting_state_effect_fails() -> None:
    text = json.dumps(response()).replace(
        '"state_effect": "NONE"',
        '"state_effect": "NONE", "state_effect": "PROPOSED"',
    )
    _, result = validate_response_text(text)
    assert "DUPLICATE_CONTRADICTORY_FIELD" in codes(result)


def test_invalid_enum_fails() -> None:
    document = response()
    document["message_type"] = "PERSONAL_OPINION"
    assert "ENUM_VALUE_INVALID" in codes(validate_response_envelope(document))


def test_self_created_authority_state_fails() -> None:
    document = response()
    document["state_effect"] = "CANONICALLY_APPROVED"
    assert "SELF_CREATED_STATE" in codes(validate_response_envelope(document))


def test_unknown_top_level_field_fails() -> None:
    document = response()
    document["private_reasoning"] = "Not a permitted envelope field."
    assert "FIELD_NAME_INVALID" in codes(validate_response_envelope(document))


def test_unauthorized_extension_name_fails() -> None:
    document = response()
    document["extensions"] = {"private_reasoning": "Not namespaced."}
    assert "UNAUTHORIZED_EXTENSION" in codes(validate_response_envelope(document))


def test_correction_cannot_replace_content_while_declaring_it_unchanged() -> None:
    original = response()
    correction = {
        "schema_version": "1.0",
        "response_id": "RSP-TEST-002",
        "supersedes": original["response_id"],
        "member_designation": "Mr. Gold",
        "canonical_role": MR_GOLD_ROLE,
        "message_type": "CORRECTION",
        "correction": "IDENTITY_PROVENANCE_CORRECTED",
        "substantive_content_changed": "NO",
        "state_effect": "NONE",
        "content": {"replacement": "Different analysis."},
    }
    result = validate_response_envelope(
        correction,
        response_index={str(original["response_id"]): original},
    )
    assert "CORRECTION_SCOPE_OVERREACH" in codes(result)


def test_correction_target_must_resolve() -> None:
    document = response()
    document.update(
        {
            "message_type": "CORRECTION",
            "supersedes": "RSP-MISSING",
            "correction": "IDENTITY_PROVENANCE_CORRECTED",
            "substantive_content_changed": "NO",
        }
    )
    result = validate_response_envelope(document)
    assert "CORRECTION_TARGET_UNRESOLVED" in codes(result)


def test_unresolved_registry_does_not_invent_identity() -> None:
    registry = copy.deepcopy(load_identity_registry())
    registry["resolution"] = "UNRESOLVED"
    result = validate_response_envelope(response(), registry=registry)
    assert result["identity"] == "UNRESOLVED_REGISTRY"
    assert "UNRESOLVED_REGISTRY" in codes(result)


def test_markdown_code_fence_is_interpretable_warning() -> None:
    text = f"```json\n{json.dumps(response())}\n```"
    _, result = validate_response_text(text)
    assert result["conformant"] is True
    assert "LEGACY_FORMATTING" in codes(result, "warnings")


def test_free_prose_outside_envelope_fails() -> None:
    _, result = validate_response_text("Commentary\n" + json.dumps(response()))
    assert "CONTENT_OUTSIDE_ENVELOPE" in codes(result)


def test_human_render_separates_conformance_from_substantive_review() -> None:
    document = response()
    result = validate_response_envelope(document)
    rendered = render_response(document, result)
    assert "Envelope: CONFORMANT" in rendered
    assert "Identity: MATCH" in rendered
    assert "Substantive review: REQUIRES HUMAN / ROLE REVIEW" in rendered


def test_registry_and_envelope_examples_are_machine_checkable() -> None:
    registry_schema = json.loads(
        (REPO_ROOT / "schemas" / "response-identity-registry.schema.json").read_text()
    )
    response_schema = json.loads(
        (REPO_ROOT / "schemas" / "response-envelope.schema.json").read_text()
    )
    assert not list(Draft202012Validator(registry_schema).iter_errors(load_identity_registry()))
    assert not list(Draft202012Validator(response_schema).iter_errors(response()))


def test_registry_roles_are_derived_from_current_role_files() -> None:
    registry = load_identity_registry()
    roles = {item["member_designation"]: item["canonical_role"] for item in registry["members"]}
    assert roles["Mr. Gold"] == MR_GOLD_ROLE
    assert roles["Blue-0"] == BLUE_0_ROLE
