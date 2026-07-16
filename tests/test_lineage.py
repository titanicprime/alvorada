from __future__ import annotations

from pathlib import Path

import pytest

from alvorada.exceptions import LineageError
from alvorada.lineage import verify_lineage_path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_valid_lineage_directory_passes() -> None:
    result = verify_lineage_path(REPO_ROOT / "examples" / "valid")
    assert result["valid"] is True


def test_invalid_lineage_file_fails() -> None:
    with pytest.raises(LineageError):
        verify_lineage_path(REPO_ROOT / "examples" / "invalid" / "broken-lineage.json")
