from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "state" / "response-identities.json"
ENVELOPE_SCHEMA = REPO_ROOT / "schemas" / "response-envelope.schema.json"


@dataclass(frozen=True)
class EnvelopeFinding:
    severity: str
    code: str
    message: str
    field: str | None = None


def _finding(severity: str, code: str, message: str, field: str | None = None) -> EnvelopeFinding:
    return EnvelopeFinding(severity, code, message, field)


def _load_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value: Any = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def load_identity_registry(path: Path | None = None) -> dict[str, Any]:
    """Load descriptive institutional identity state without inventing missing identities."""
    return _load_object(path or DEFAULT_REGISTRY)


def _schema_findings(envelope: dict[str, Any]) -> list[EnvelopeFinding]:
    schema = _load_object(ENVELOPE_SCHEMA)
    validator = Draft202012Validator(schema)
    findings: list[EnvelopeFinding] = []
    seen: set[tuple[str, str | None]] = set()
    for error in sorted(validator.iter_errors(envelope), key=lambda item: list(item.absolute_path)):
        path = ".".join(str(item) for item in error.absolute_path) or None
        if error.validator == "required":
            missing = str(error.message).split("'")[1]
            code = (
                "IDENTITY_MISSING" if missing == "member_designation" else "REQUIRED_FIELD_MISSING"
            )
            path = missing
        elif error.validator == "additionalProperties":
            code = "UNAUTHORIZED_EXTENSION" if path == "extensions" else "FIELD_NAME_INVALID"
        elif error.validator in {"enum", "const"}:
            code = (
                "SELF_CREATED_STATE"
                if path and path.endswith("state_effect")
                else "ENUM_VALUE_INVALID"
            )
        else:
            code = "FIELD_NAME_INVALID"
        key = (code, path)
        if key not in seen:
            findings.append(_finding("ERROR", code, error.message, path))
            seen.add(key)
    return findings


def _identity_state(
    envelope: dict[str, Any], registry: dict[str, Any], findings: list[EnvelopeFinding]
) -> str:
    if registry.get("resolution") != "RESOLVED":
        findings.append(
            _finding(
                "ERROR",
                "UNRESOLVED_REGISTRY",
                "Institutional identity registry cannot currently resolve identities.",
            )
        )
        return "UNRESOLVED_REGISTRY"

    members = [item for item in registry.get("members", []) if isinstance(item, dict)]
    designation = envelope.get("member_designation")
    role = envelope.get("canonical_role")
    if not isinstance(designation, str) or not designation:
        return "UNKNOWN_MEMBER"

    member = next((item for item in members if item.get("member_designation") == designation), None)
    if member is None:
        normalized = "".join(character.lower() for character in designation if character.isalnum())
        near_match = next(
            (
                item
                for item in members
                if normalized
                in {
                    "".join(
                        character.lower()
                        for character in str(item.get(field, ""))
                        if character.isalnum()
                    )
                    for field in ("member_designation", "state_member_id")
                }
            ),
            None,
        )
        if near_match is not None:
            findings.append(
                _finding(
                    "ERROR",
                    "IDENTITY_MISMATCH",
                    f"Member designation {designation!r} does not exactly match "
                    f"{near_match.get('member_designation')!r}.",
                    "member_designation",
                )
            )
            return "MISMATCH"
        findings.append(
            _finding(
                "ERROR",
                "UNKNOWN_MEMBER",
                f"Member designation {designation!r} is not registered.",
                "member_designation",
            )
        )
        return "UNKNOWN_MEMBER"

    registered_roles = {str(item.get("canonical_role")) for item in members}
    expected_role = member.get("canonical_role")
    if not isinstance(role, str) or not role:
        return "UNKNOWN_ROLE"
    if role == expected_role:
        return "MATCH"
    if role not in registered_roles:
        findings.append(
            _finding(
                "ERROR",
                "SELF_CREATED_ROLE",
                f"Canonical role {role!r} is not registered.",
                "canonical_role",
            )
        )
        return "UNKNOWN_ROLE"
    findings.append(
        _finding(
            "ERROR",
            "ROLE_MISMATCH",
            f"{designation!r} is registered with role {expected_role!r}, not {role!r}.",
            "canonical_role",
        )
    )
    return "MISMATCH"


def _correction_checks(
    envelope: dict[str, Any],
    response_index: dict[str, dict[str, Any]],
    findings: list[EnvelopeFinding],
) -> None:
    if envelope.get("message_type") != "CORRECTION":
        return
    target_id = envelope.get("supersedes")
    target = response_index.get(str(target_id))
    if target is None:
        findings.append(
            _finding(
                "ERROR",
                "CORRECTION_TARGET_UNRESOLVED",
                f"Correction target {target_id!r} cannot be resolved.",
                "supersedes",
            )
        )
        return

    unchanged = envelope.get("substantive_content_changed") == "NO"
    replacement_present = "content" in envelope
    replacement_changed = replacement_present and envelope.get("content") != target.get("content")
    if unchanged and (
        replacement_changed or envelope.get("correction") == "SUBSTANTIVE_CONTENT_CORRECTED"
    ):
        findings.append(
            _finding(
                "ERROR",
                "CORRECTION_SCOPE_OVERREACH",
                "Correction declares unchanged substantive content but replaces or corrects it.",
                "content",
            )
        )
    if envelope.get("substantive_content_changed") == "YES" and not replacement_present:
        findings.append(
            _finding(
                "ERROR",
                "REQUIRED_FIELD_MISSING",
                "A substantive correction must provide replacement content.",
                "content",
            )
        )


def validate_response_envelope(
    envelope: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
    response_index: dict[str, dict[str, Any]] | None = None,
    initial_findings: list[EnvelopeFinding] | None = None,
) -> dict[str, Any]:
    """Validate protocol conformance without making a substantive or authority judgment."""
    findings = list(initial_findings or [])
    findings.extend(_schema_findings(envelope))
    identity = _identity_state(envelope, registry or load_identity_registry(), findings)
    _correction_checks(envelope, response_index or {}, findings)

    serialized = [asdict(item) for item in findings]
    errors = [item for item in serialized if item["severity"] == "ERROR"]
    warnings = [item for item in serialized if item["severity"] == "WARNING"]
    informational = [item for item in serialized if item["severity"] == "INFORMATIONAL"]
    return {
        "conformant": not errors,
        "identity": identity,
        "errors": errors,
        "warnings": warnings,
        "informational": informational,
        "substantive_review": "REQUIRES HUMAN / ROLE REVIEW",
    }


def validate_response_text(
    text: str,
    *,
    registry: dict[str, Any] | None = None,
    response_index: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Parse a response while preserving duplicate-field and decoration findings."""
    findings: list[EnvelopeFinding] = []
    payload = text.strip()
    if payload.startswith("```"):
        lines = payload.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            payload = "\n".join(lines[1:-1])
            findings.append(
                _finding(
                    "WARNING",
                    "LEGACY_FORMATTING",
                    "Markdown code-fence decoration is interpretable but not part of the envelope.",
                )
            )

    duplicates: list[tuple[str, bool]] = []

    def detect_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append((key, result[key] != value))
            result[key] = value
        return result

    try:
        value: Any = json.loads(payload, object_pairs_hook=detect_pairs)
    except json.JSONDecodeError as error:
        findings.append(
            _finding(
                "ERROR",
                "CONTENT_OUTSIDE_ENVELOPE",
                f"Response is not a single structured envelope: {error.msg}.",
            )
        )
        empty_result = validate_response_envelope(
            {},
            registry=registry,
            response_index=response_index,
            initial_findings=findings,
        )
        return None, empty_result

    if not isinstance(value, dict):
        findings.append(
            _finding(
                "ERROR",
                "CONTENT_OUTSIDE_ENVELOPE",
                "Response must contain one envelope object.",
            )
        )
        return None, validate_response_envelope(
            {},
            registry=registry,
            response_index=response_index,
            initial_findings=findings,
        )

    for field, contradictory in duplicates:
        if contradictory:
            findings.append(
                _finding(
                    "ERROR",
                    "DUPLICATE_CONTRADICTORY_FIELD",
                    f"Field {field!r} is repeated with contradictory values.",
                    field,
                )
            )
        else:
            findings.append(
                _finding(
                    "INFORMATIONAL",
                    "DUPLICATE_EQUIVALENT_FIELD",
                    f"Equivalent duplicate field {field!r} should be removed.",
                    field,
                )
            )
    return value, validate_response_envelope(
        value,
        registry=registry,
        response_index=response_index,
        initial_findings=findings,
    )


def validate_response_file(
    path: Path,
    *,
    registry: dict[str, Any] | None = None,
    response_index: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    return validate_response_text(
        path.read_text(encoding="utf-8"),
        registry=registry,
        response_index=response_index,
    )


def render_response(envelope: dict[str, Any], result: dict[str, Any]) -> str:
    """Render conformance separately from the required substantive human review."""
    responding_to = envelope.get("in_response_to") or envelope.get("supersedes") or "UNRESOLVED"
    envelope_state = "CONFORMANT" if result["conformant"] else "NONCONFORMANT"
    return "\n".join(
        [
            f"Response: {envelope.get('response_id', 'UNRESOLVED')}",
            f"Member: {envelope.get('member_designation', 'UNRESOLVED')}",
            f"Role: {envelope.get('canonical_role', 'UNRESOLVED')}",
            f"Responding to: {responding_to}",
            f"Envelope: {envelope_state}",
            f"Identity: {result['identity']}",
            f"State effect: {envelope.get('state_effect', 'UNRESOLVED')}",
            f"Substantive review: {result['substantive_review']}",
        ]
    )
