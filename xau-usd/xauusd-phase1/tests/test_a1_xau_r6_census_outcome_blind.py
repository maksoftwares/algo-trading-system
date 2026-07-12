from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_a1_xau_r6_outcome_blind_census as V  # noqa: E402


def schema() -> dict:
    return json.loads((ROOT / "docs" / "A1_XAU_R6_OUTCOME_BLIND_CENSUS_SCHEMA_V1.json").read_text())


def test_closed_schema_is_outcome_blind() -> None:
    V.validate_closed_schema(schema())
    properties = set(schema()["properties"])
    assert not properties & V.FORBIDDEN_FIELDS


def test_forbidden_field_and_partial_exclusion_are_rejected() -> None:
    bad = schema()
    bad["properties"]["profit"] = {"type": "number"}
    bad["required"].append("profit")
    with pytest.raises(ValueError, match="forbidden"):
        V.validate_closed_schema(bad)
    bad = schema()
    bad["properties"]["availability_status"] = {"type": "string"}
    with pytest.raises(ValueError, match="partial"):
        V.validate_closed_schema(bad)


def test_c2_file_boundary_is_exact() -> None:
    V.validate_changed_files(sorted(V.ALLOWED_C2_FILES))
    with pytest.raises(ValueError, match="outside"):
        V.validate_changed_files(["mt5/Experts/forbidden.mq5"])


def test_prefix_invariance_rejects_changed_prior_row() -> None:
    original = {"candidate_id": "a", "entry_tick_sequence": 10, "entry_tick_time": "2020-01-01T00:00:00"}
    V.validate_prefix_invariance([original], [original, {"candidate_id": "b"}])
    with pytest.raises(ValueError, match="prefix"):
        V.validate_prefix_invariance([original], [{"candidate_id": "a", "entry_tick_sequence": 11, "entry_tick_time": "2020-01-01T00:00:00"}])
    new_inside_prefix = {"candidate_id": "b", "entry_tick_time": "2020-01-01T00:30:00"}
    with pytest.raises(ValueError, match="inside"):
        V.validate_prefix_invariance([original], [original, new_inside_prefix], prefix_end=datetime(2020, 1, 1, 1))


def test_scripts_have_no_runtime_or_result_surface() -> None:
    paths = [ROOT / path for path in V.ALLOWED_C2_FILES if path.startswith("scripts/")]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for forbidden in ("argparse", "metatrader", "order_send", "account_login", "--live", "--demo"):
        assert forbidden not in text
