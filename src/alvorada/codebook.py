from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from alvorada.canonicalize import load_json_file
from alvorada.dictionary import DICTIONARY_PATH, dictionary_terms, load_dictionary
from alvorada.exceptions import CodebookError

REPO_ROOT = Path(__file__).resolve().parents[2]
CODEBOOK_SCHEMA_PATH = REPO_ROOT / "schema" / "odex-imx-codebook-v0.1.schema.json"


def load_codebook(path: Path) -> dict[str, Any]:
    data = load_json_file(path)
    return data if isinstance(data, dict) else {}


def codebook_check(path: Path, *, dictionary_path: Path | None = None) -> dict[str, Any]:
    schema = load_json_file(CODEBOOK_SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    codebook = load_codebook(path)
    errors = [error.message for error in sorted(validator.iter_errors(codebook), key=str)]
    if errors:
        raise CodebookError("; ".join(errors))
    entries = codebook["entries"]
    codes = list(entries.keys())
    terms = list(entries.values())
    if len(codes) != len(set(codes)):
        raise CodebookError("Duplicate codes are invalid.")
    if len(terms) != len(set(terms)):
        raise CodebookError("Duplicate canonical term mappings are invalid.")
    dictionary = load_dictionary(dictionary_path or DICTIONARY_PATH)
    if codebook["dictionary_version"] != dictionary["version"]:
        raise CodebookError(
            "Codebook dictionary version does not match canonical dictionary version."
        )
    unknown_terms = sorted(set(terms) - dictionary_terms(dictionary_path or DICTIONARY_PATH))
    if unknown_terms:
        raise CodebookError(f"Unknown canonical terms in codebook: {', '.join(unknown_terms)}")
    return {
        "valid": True,
        "codebook_id": codebook["codebook_id"],
        "dictionary_version": codebook["dictionary_version"],
        "entry_count": len(entries),
        "errors": [],
        "warnings": [],
    }


def _encode_value(value: Any, reverse_entries: dict[str, str]) -> Any:
    if isinstance(value, dict):
        encoded: dict[str, Any] = {}
        for key, item in value.items():
            code = reverse_entries.get(key)
            if code is None:
                raise CodebookError(f"Unknown canonical term for encoding: {key}")
            encoded[code] = _encode_value(item, reverse_entries)
        return encoded
    if isinstance(value, list):
        return [_encode_value(item, reverse_entries) for item in value]
    return value


def _decode_value(value: Any, entries: dict[str, str]) -> Any:
    if isinstance(value, dict):
        decoded: dict[str, Any] = {}
        for key, item in value.items():
            canonical_term = entries.get(key)
            if canonical_term is None:
                raise CodebookError(f"Unknown code for decoding: {key}")
            decoded[canonical_term] = _decode_value(item, entries)
        return decoded
    if isinstance(value, list):
        return [_decode_value(item, entries) for item in value]
    return value


def encode_document(document: Any, codebook_path: Path) -> dict[str, Any]:
    codebook = load_codebook(codebook_path)
    codebook_check(codebook_path)
    reverse_entries = {value: key for key, value in codebook["entries"].items()}
    return {
        "codebook_id": codebook["codebook_id"],
        "dictionary_version": codebook["dictionary_version"],
        "payload": _encode_value(document, reverse_entries),
    }


def decode_document(document: dict[str, Any], codebook_path: Path) -> Any:
    codebook = load_codebook(codebook_path)
    codebook_check(codebook_path)
    if document.get("codebook_id") != codebook["codebook_id"]:
        raise CodebookError("Encoded payload codebook_id does not match the supplied codebook.")
    if document.get("dictionary_version") != codebook["dictionary_version"]:
        raise CodebookError(
            "Encoded payload dictionary version does not match the supplied codebook."
        )
    payload = document.get("payload")
    return _decode_value(payload, codebook["entries"])
