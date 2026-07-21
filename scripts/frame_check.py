"""
frame_check.py — FRAME-stage failure pattern check for Alvorada.

Loads a work item (YAML or JSON) and checks it against ACTIVE failure patterns
using keyword matching. Returns matched patterns as warnings.

Usage:
    python scripts/frame_check.py --work-item <path> --failure-patterns <path>
    python scripts/frame_check.py --work-item <path> --failure-patterns <path> --output <path>
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Install it with: pip install pyyaml")


VALID_RESULTS = {"helped", "harmed", "neutral", "unclear"}

SEARCHABLE_FIELDS = ["title", "problem_statement", "constraints", "output_contract"]


def load_file(path: Path) -> dict:
    """Load a YAML or JSON file and return its contents as a dict."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".json"}:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            sys.exit(f"Error: could not parse JSON file '{path}': {exc}")
    else:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            sys.exit(f"Error: could not parse YAML file '{path}': {exc}")
        if not isinstance(data, dict):
            sys.exit(f"Error: expected a mapping at the top level of '{path}'")
        return data


def load_failure_patterns(path: Path) -> list:
    """Load failure patterns from a YAML file."""
    text = path.read_text(encoding="utf-8")
    try:
        patterns = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        sys.exit(f"Error: could not parse failure patterns '{path}': {exc}")
    if patterns is None:
        return []
    if not isinstance(patterns, list):
        sys.exit(f"Error: failure patterns file must be a YAML list in '{path}'")
    return patterns


def build_search_text(work_item: dict) -> str:
    """Combine searchable fields from the work item into a single lowercase string."""
    parts = []
    for field in SEARCHABLE_FIELDS:
        value = work_item.get(field)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(v) for v in value)
    return " ".join(parts).lower()


def derive_keywords(conditions: str) -> list:
    """Derive conservative keywords from a conditions string.

    Extracts words of 4+ characters, excluding common stop words.
    This is a conservative heuristic; explicit keywords in the pattern
    take precedence when provided.
    """
    stop_words = {
        "this", "that", "with", "from", "have", "been", "will", "when",
        "where", "which", "their", "there", "about", "after", "before",
        "under", "using", "more", "than", "also", "into", "such", "each",
        "both", "used", "being", "they", "them", "then", "some",
    }
    words = re.findall(r"[a-zA-Z]{4,}", conditions.lower())
    return [w for w in words if w not in stop_words]


def check_pattern(pattern: dict, search_text: str) -> bool:
    """Return True if the pattern matches the search text."""
    # Use explicit keywords if provided; otherwise derive from conditions.
    if "keywords" in pattern and isinstance(pattern["keywords"], list):
        keywords = [str(k).lower() for k in pattern["keywords"]]
    else:
        conditions = pattern.get("conditions", "")
        keywords = derive_keywords(str(conditions))

    if not keywords:
        return False

    return any(kw in search_text for kw in keywords)


def run_frame_check(work_item: dict, patterns: list) -> list:
    """Return ACTIVE patterns that match the work item."""
    search_text = build_search_text(work_item)
    matched = []
    for pattern in patterns:
        if not isinstance(pattern, dict):
            continue
        if pattern.get("status") != "ACTIVE":
            continue
        if check_pattern(pattern, search_text):
            matched.append(pattern)
    return matched


def format_warning(pattern: dict) -> str:
    lines = [
        f"  [WARNING] {pattern.get('asset_id', 'UNKNOWN')}",
        f"  Statement : {pattern.get('statement', '')}",
        f"  Conditions: {pattern.get('conditions', '')}",
        f"  Origin    : {pattern.get('origin_mission', '')}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check a work item against Alvorada failure patterns at FRAME stage."
    )
    parser.add_argument(
        "--work-item",
        required=True,
        metavar="PATH",
        help="Path to the work item (YAML or JSON)",
    )
    parser.add_argument(
        "--failure-patterns",
        required=True,
        metavar="PATH",
        help="Path to failure-patterns.yaml",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        default=None,
        help="Optional output path; writes a copy of the work item with failure_memory added",
    )
    args = parser.parse_args()

    work_item_path = Path(args.work_item)
    patterns_path = Path(args.failure_patterns)

    if not work_item_path.exists():
        sys.exit(f"Error: work item not found: '{work_item_path}'")
    if not patterns_path.exists():
        sys.exit(f"Error: failure patterns file not found: '{patterns_path}'")

    work_item = load_file(work_item_path)
    patterns = load_failure_patterns(patterns_path)

    matched = run_frame_check(work_item, patterns)

    if matched:
        print(f"FRAME CHECK: {len(matched)} failure pattern(s) matched.\n")
        print("Note: matches are keyword-based; semantic certainty is not claimed.\n")
        for pattern in matched:
            print(format_warning(pattern))
            print()
    else:
        print("FRAME CHECK: no failure patterns matched.")

    if args.output is not None:
        output_path = Path(args.output)
        output_data = dict(work_item)
        output_data["failure_memory"] = [
            {
                "asset_id": p.get("asset_id"),
                "statement": p.get("statement"),
                "origin_mission": p.get("origin_mission"),
            }
            for p in matched
        ]
        output_path.write_text(
            yaml.dump(output_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"Output written to: {output_path}")

    if matched:
        sys.exit(0)  # Warnings surfaced; not an error.


if __name__ == "__main__":
    main()
