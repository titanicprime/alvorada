from __future__ import annotations

from pathlib import Path

import pytest

from alvorada.canonicalize import load_json_file
from alvorada.codebook import codebook_check, decode_document, encode_document
from alvorada.exceptions import CodebookError

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_codebook_round_trip() -> None:
    message = load_json_file(REPO_ROOT / "examples" / "valid" / "ack.json")
    codebook = REPO_ROOT / "codebooks" / "protocol-codebook.json"
    encoded = encode_document(message, codebook)
    decoded = decode_document(encoded, codebook)
    assert decoded == message


def test_unknown_codes_fail_closed() -> None:
    codebook = REPO_ROOT / "codebooks" / "protocol-codebook.json"
    with pytest.raises(CodebookError):
        decode_document(
            {
                "codebook_id": "ALVORADA-PROTOCOL-0.1",
                "dictionary_version": "0.1.0",
                "payload": {"ZZ": 1},
            },
            codebook,
        )


def test_version_skew_fails() -> None:
    codebook = REPO_ROOT / "codebooks" / "protocol-codebook.json"
    with pytest.raises(CodebookError):
        decode_document(
            {
                "codebook_id": "ALVORADA-PROTOCOL-0.1",
                "dictionary_version": "9.9.9",
                "payload": {},
            },
            codebook,
        )


def test_codebook_check_passes() -> None:
    result = codebook_check(REPO_ROOT / "codebooks" / "protocol-codebook.json")
    assert result["valid"] is True
