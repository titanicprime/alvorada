from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from alvorada.canonicalize import load_json_file
from alvorada.delta import apply_operations
from alvorada.exceptions import DeltaError, ValidationError
from alvorada.hashing import verify_hash_data

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schema"


def _schema_registry() -> Registry[Any]:
    registry: Registry[Any] = Registry()
    for schema_path in SCHEMA_DIR.glob("*.json"):
        schema = load_json_file(schema_path)
        if isinstance(schema, dict) and "$id" in schema:
            registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return registry


def load_schema(name: str) -> dict[str, Any]:
    schema = load_json_file(SCHEMA_DIR / name)
    return schema if isinstance(schema, dict) else {}


def _pick_schema(document: dict[str, Any]) -> str:
    response_type = document.get("header", {}).get("response_type")
    if response_type == "ACK":
        return "odex-imx-ack-v0.2.schema.json"
    if response_type in {
        "MISSION_COMPLETE",
        "MISSION_FAILED",
        "BLOCKED",
        "REQUEST_CLARIFICATION",
        "STATE_UPDATE",
        "PROTOCOL_EXCEPTION",
    }:
        return "odex-imx-response-v0.2.schema.json"
    return "odex-imx-v0.2.schema.json"


def _semantic_checks(document: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    claims = document.get("claims", [])
    for claim in claims:
        role_assignment = claim.get("role_assignment")
        if isinstance(role_assignment, dict) and (
            role_assignment.get("subject") == role_assignment.get("assigned_by")
        ):
            errors.append("Roles must not be self-assigned.")
    if document.get("header", {}).get("response_type") == "PROTOCOL_EXCEPTION" and not document.get(
        "conflicts"
    ):
        errors.append("PROTOCOL_EXCEPTION messages must include at least one conflict record.")
    if document.get("delta", {}).get("operations"):
        try:
            apply_operations({}, document["delta"]["operations"])
        except DeltaError as error:
            errors.append(str(error))
    try:
        verify_hash_data(document)
    except Exception as error:
        errors.append(str(error))
    return errors, warnings


def validate_document(path: Path) -> dict[str, Any]:
    document = load_json_file(path)
    if not isinstance(document, dict):
        raise ValidationError("Document must be a JSON object.")
    schema_name = _pick_schema(document)
    schema = load_schema(schema_name)
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=FormatChecker(),
    )
    errors = [
        error.message
        for error in sorted(
            validator.iter_errors(document),
            key=lambda item: list(item.absolute_path),
        )
    ]
    semantic_errors, warnings = _semantic_checks(document) if not errors else ([], [])
    all_errors = errors + semantic_errors
    return {
        "valid": not all_errors,
        "schema": schema_name.removesuffix(".schema.json"),
        "errors": all_errors,
        "warnings": warnings,
    }


def validate_directory(path: Path) -> dict[str, Any]:
    results = []
    for file_path in sorted(path.rglob("*.json")):
        results.append({"path": str(file_path), **validate_document(file_path)})
    return {
        "valid": all(item["valid"] for item in results),
        "schema": "directory",
        "errors": [],
        "warnings": [],
        "results": results,
    }
