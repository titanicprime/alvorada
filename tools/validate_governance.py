from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from alvorada.governance import validate_governance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate governance records without authorizing them."
    )
    parser.add_argument("document", type=Path)
    args = parser.parse_args()
    with args.document.open(encoding="utf-8") as stream:
        document: Any = json.load(stream)
    if not isinstance(document, dict):
        parser.error("document must contain a JSON object")
    result = validate_governance(document)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
