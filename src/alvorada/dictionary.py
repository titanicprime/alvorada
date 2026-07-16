from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from alvorada.canonicalize import load_json_file
from alvorada.exceptions import DictionaryError

REPO_ROOT = Path(__file__).resolve().parents[2]
DICTIONARY_PATH = REPO_ROOT / "dictionary" / "canonical-dictionary.json"
CHANGELOG_PATH = REPO_ROOT / "dictionary" / "changelog.jsonl"
DICTIONARY_SCHEMA_PATH = REPO_ROOT / "schema" / "odex-imx-dictionary-v0.1.schema.json"


def load_dictionary(path: Path | None = None) -> dict[str, Any]:
    data = load_json_file(path or DICTIONARY_PATH)
    return data if isinstance(data, dict) else {}


def dictionary_terms(path: Path | None = None) -> set[str]:
    dictionary = load_dictionary(path)
    return {term["canonical_term"] for term in dictionary.get("terms", [])}


def dictionary_check(
    path: Path | None = None, changelog_path: Path | None = None
) -> dict[str, Any]:
    dictionary_path = path or DICTIONARY_PATH
    changelog = changelog_path or CHANGELOG_PATH
    dictionary = load_dictionary(dictionary_path)
    schema = load_json_file(DICTIONARY_SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = [error.message for error in sorted(validator.iter_errors(dictionary), key=str)]
    if errors:
        raise DictionaryError("; ".join(errors))
    terms = dictionary.get("terms", [])
    term_ids = [term["term_id"] for term in terms]
    canonical_terms = [term["canonical_term"] for term in terms]
    if len(term_ids) != len(set(term_ids)):
        raise DictionaryError("Duplicate term_id entries are not allowed.")
    if len(canonical_terms) != len(set(canonical_terms)):
        raise DictionaryError("Duplicate canonical terms are not allowed.")
    changelog_entries = []
    with changelog.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                changelog_entries.append(json.loads(line))
    recorded_term_ids = {
        term_id for entry in changelog_entries for term_id in entry.get("term_ids", [])
    }
    missing = sorted(set(term_ids) - recorded_term_ids)
    if missing:
        raise DictionaryError(f"Missing changelog entries for terms: {', '.join(missing)}")
    return {
        "valid": True,
        "dictionary_id": dictionary["dictionary_id"],
        "version": dictionary["version"],
        "term_count": len(terms),
        "errors": [],
        "warnings": [],
    }
