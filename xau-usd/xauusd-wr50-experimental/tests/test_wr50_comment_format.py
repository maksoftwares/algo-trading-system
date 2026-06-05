from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_wr50_registry import build_short_comment, validate_short_comment


def test_wr50_short_comment_is_broker_safe() -> None:
    comment = build_short_comment("BEV0", "R240604A")
    assert comment == "WR50|BEV0|R240604A"
    assert validate_short_comment(comment, "BEV0", "R240604A") == []
    assert len(comment) <= 31


def test_comment_over_31_chars_fails() -> None:
    comment = build_short_comment("BEV0", "R240604A_TOO_LONG_FOR_MT5_COMMENT")
    errors = validate_short_comment(comment, "BEV0", "R240604A_TOO_LONG_FOR_MT5_COMMENT")
    assert "comment length exceeds 31 chars" in errors


def test_missing_wr50_prefix_fails() -> None:
    errors = validate_short_comment("BAD|BEV0|R240604A", "BEV0", "R240604A")
    assert "comment must start with WR50|" in errors

