from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from alvorada.canonicalize import canonicalize_file, load_json_file
from alvorada.codebook import codebook_check, decode_document, encode_document
from alvorada.delta import apply_operations
from alvorada.dictionary import REPO_ROOT, dictionary_check
from alvorada.exceptions import AlvoradaError
from alvorada.hashing import hash_file, verify_hash_file
from alvorada.lineage import verify_lineage_path
from alvorada.validator import validate_directory, validate_document


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alvorada")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("file")

    validate_directory_parser = subparsers.add_parser("validate-directory")
    validate_directory_parser.add_argument("path")

    canonicalize = subparsers.add_parser("canonicalize")
    canonicalize.add_argument("file")

    hash_parser = subparsers.add_parser("hash")
    hash_parser.add_argument("file")

    verify_hash = subparsers.add_parser("verify-hash")
    verify_hash.add_argument("file")

    encode = subparsers.add_parser("encode")
    encode.add_argument("file")
    encode.add_argument("--codebook", required=True)

    decode = subparsers.add_parser("decode")
    decode.add_argument("file")
    decode.add_argument("--codebook", required=True)

    apply_deltas = subparsers.add_parser("apply-deltas")
    apply_deltas.add_argument("base")
    apply_deltas.add_argument("delta_file")

    verify_lineage = subparsers.add_parser("verify-lineage")
    verify_lineage.add_argument("path")

    subparsers.add_parser("dictionary-check")
    subparsers.add_parser("codebook-check")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_document(Path(args.file))
            _print_json(result)
            return 0 if result["valid"] else 1
        if args.command == "validate-directory":
            result = validate_directory(Path(args.path))
            _print_json(result)
            return 0 if result["valid"] else 1
        if args.command == "canonicalize":
            sys.stdout.buffer.write(canonicalize_file(Path(args.file)))
            sys.stdout.buffer.write(b"\n")
            return 0
        if args.command == "hash":
            _print_json({"sha256": hash_file(Path(args.file))})
            return 0
        if args.command == "verify-hash":
            verify_hash_file(Path(args.file))
            _print_json({"valid": True, "errors": [], "warnings": []})
            return 0
        if args.command == "encode":
            payload = encode_document(load_json_file(Path(args.file)), Path(args.codebook))
            _print_json(payload)
            return 0
        if args.command == "decode":
            payload = decode_document(load_json_file(Path(args.file)), Path(args.codebook))
            _print_json(payload)
            return 0
        if args.command == "apply-deltas":
            base = load_json_file(Path(args.base))
            if not isinstance(base, dict):
                raise AlvoradaError("Base file must contain a JSON object.")
            delta_document = load_json_file(Path(args.delta_file))
            if not isinstance(delta_document, dict):
                raise AlvoradaError("Delta file must contain a JSON object.")
            operations = delta_document.get("operations")
            if operations is None and isinstance(delta_document.get("delta"), dict):
                operations = delta_document["delta"].get("operations", [])
            if not isinstance(operations, list):
                raise AlvoradaError("Delta file does not contain operations.")
            _print_json(apply_operations(base, operations))
            return 0
        if args.command == "verify-lineage":
            result = verify_lineage_path(Path(args.path))
            _print_json(result)
            return 0 if result["valid"] else 1
        if args.command == "dictionary-check":
            _print_json(dictionary_check())
            return 0
        if args.command == "codebook-check":
            results = []
            for codebook_path in sorted((REPO_ROOT / "codebooks").glob("*.json")):
                results.append({"path": str(codebook_path), **codebook_check(codebook_path)})
            _print_json(
                {
                    "valid": all(item["valid"] for item in results),
                    "errors": [],
                    "warnings": [],
                    "results": results,
                }
            )
            return 0
    except AlvoradaError as error:
        _print_json({"valid": False, "errors": [str(error)], "warnings": []})
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
