from __future__ import annotations

from alvorada.dictionary import dictionary_check


def test_dictionary_check_passes() -> None:
    result = dictionary_check()
    assert result["valid"] is True
    assert result["term_count"] >= 20
