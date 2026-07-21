"""
validate_state.py — Validate Alvorada state files.

Checks:
- state/failure-patterns.yaml against failure-pattern.schema.json
- missions/*/collection.yaml against collection.schema.json
- state/asset-use-log.csv result values
- duplicate asset IDs in failure-patterns.yaml
- every ACTIVE failure pattern has an origin_mission
- state/current.yaml member names are known values

Returns exit code 0 on success, nonzero on failure.
"""

import csv
import glob
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Install it with: pip install pyyaml")

try:
    import jsonschema
except ImportError:
    sys.exit("Error: jsonschema is required. Install it with: pip install jsonschema")


REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_RESULT_VALUES = {"helped", "harmed", "neutral", "unclear"}
KNOWN_MEMBERS = {"MR_GOLD", "BLUE_0", "SIENNA_4"}

errors: list = []


def err(message: str) -> None:
    errors.append(message)
    print(f"ERROR: {message}", file=sys.stderr)


def load_schema(name: str) -> dict:
    path = REPO_ROOT / "schemas" / name
    if not path.exists():
        sys.exit(f"Error: schema file not found: '{path}'")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_against_schema(data, schema: dict, label: str) -> None:
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(data):
        err(f"{label}: {error.message} (at {list(error.path)})")


def validate_failure_patterns() -> None:
    path = REPO_ROOT / "state" / "failure-patterns.yaml"
    if not path.exists():
        err(f"Missing file: {path}")
        return

    schema = load_schema("failure-pattern.schema.json")
    patterns = load_yaml(path)

    if patterns is None:
        err(f"{path}: file is empty or null")
        return
    if not isinstance(patterns, list):
        err(f"{path}: expected a list of patterns")
        return

    seen_ids: set = set()
    for i, pattern in enumerate(patterns):
        label = f"failure-patterns.yaml[{i}]"
        if not isinstance(pattern, dict):
            err(f"{label}: not a mapping")
            continue

        validate_against_schema(pattern, schema, label)

        asset_id = pattern.get("asset_id")
        if asset_id in seen_ids:
            err(f"{label}: duplicate asset_id '{asset_id}'")
        elif asset_id:
            seen_ids.add(asset_id)

        if pattern.get("status") == "ACTIVE" and not pattern.get("origin_mission"):
            err(f"{label}: ACTIVE pattern '{asset_id}' is missing origin_mission")


def validate_collections() -> None:
    schema = load_schema("collection.schema.json")
    collection_paths = list(
        REPO_ROOT.glob("missions/*/collection.yaml")
    )
    if not collection_paths:
        print("INFO: no collection.yaml files found — skipping collection validation")
        return

    for path in collection_paths:
        data = load_yaml(path)
        if data is None:
            err(f"{path}: empty file")
            continue
        validate_against_schema(data, schema, str(path.relative_to(REPO_ROOT)))


def validate_asset_use_log() -> None:
    path = REPO_ROOT / "state" / "asset-use-log.csv"
    if not path.exists():
        err(f"Missing file: {path}")
        return

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            err(f"{path}: file has no header row")
            return
        for i, row in enumerate(reader, start=2):
            result = row.get("result", "").strip()
            if result and result not in VALID_RESULT_VALUES:
                err(
                    f"asset-use-log.csv row {i}: invalid result '{result}'. "
                    f"Must be one of: {', '.join(sorted(VALID_RESULT_VALUES))}"
                )


def validate_current_yaml() -> None:
    path = REPO_ROOT / "state" / "current.yaml"
    if not path.exists():
        err(f"Missing file: {path}")
        return

    data = load_yaml(path)
    if not isinstance(data, dict):
        err(f"{path}: expected a mapping")
        return

    members_block = data.get("members")
    if members_block and isinstance(members_block, dict):
        expected = members_block.get("expected", [])
        if isinstance(expected, list):
            for name in expected:
                if name not in KNOWN_MEMBERS:
                    err(
                        f"current.yaml: unknown member name '{name}'. "
                        f"Known members: {', '.join(sorted(KNOWN_MEMBERS))}"
                    )


def main() -> None:
    print("Validating Alvorada state files...")

    validate_failure_patterns()
    validate_collections()
    validate_asset_use_log()
    validate_current_yaml()

    if errors:
        print(f"\nValidation failed with {len(errors)} error(s).")
        sys.exit(1)
    else:
        print("All validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
