from __future__ import annotations

import json
import sys
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
    original = {"candidate_id": "a", "entry_tick_sequence": 10}
    V.validate_prefix_invariance([original], [original, {"candidate_id": "b"}])
    with pytest.raises(ValueError, match="prefix"):
        V.validate_prefix_invariance([original], [{"candidate_id": "a", "entry_tick_sequence": 11}])


def test_scripts_have_no_runtime_or_result_surface() -> None:
    paths = [ROOT / path for path in V.ALLOWED_C2_FILES if path.startswith("scripts/")]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for forbidden in ("argparse", "metatrader", "order_send", "account_login", "--live", "--demo"):
        assert forbidden not in text
