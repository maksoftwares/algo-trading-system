from __future__ import annotations

import json
import sys
import ast
import hashlib
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_a1_xau_r6_outcome_blind_census as V  # noqa: E402
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402


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
    new_inside_prefix = {"candidate_id": "b", "entry_tick_time": "2020-01-01T00:30:00", "entry_tick_sequence": 11}
    with pytest.raises(ValueError, match="inside"):
        V.validate_prefix_invariance(
            [original], [original, new_inside_prefix], prefix_cutoff=R.PrefixCutoff(datetime(2020, 1, 1, 1), 99),
        )


def test_detector_prefix_invariance_is_bidirectional_for_exclusions() -> None:
    first = R.TerminalAnchor(datetime(2020, 1, 1), datetime(2020, 1, 1, 1), "IMPULSE_REJECTED")
    introduced = R.TerminalAnchor(datetime(2020, 1, 1, 2), datetime(2020, 1, 1, 3), "DATA_UNAVAILABLE")
    empty_incidence = R.incidence_report([])

    def detector(*, extended: bool) -> R.Detection:
        anchors = (first, introduced) if extended else (first,)
        return R.Detection((), {status: 0 for status in R.TERMINAL_STATUSES}, anchors, empty_incidence, R.locked_final_status(empty_incidence), {})

    with pytest.raises(ValueError, match="terminal prefix"):
        V.validate_detector_prefix_invariance(
            detector, {"extended": False}, {"extended": True},
            prefix_cutoff=R.PrefixCutoff(datetime(2020, 1, 1, 4), 99),
        )


def test_prefix_cutoff_uses_absolute_sequence_within_same_second() -> None:
    original = {"candidate_id": "a", "entry_tick_time": "2020-01-01T00:00:00", "entry_tick_sequence": 10}
    later = {"candidate_id": "b", "entry_tick_time": "2020-01-01T00:00:00", "entry_tick_sequence": 11}
    V.validate_prefix_invariance(
        [original], [original, later], prefix_cutoff=R.PrefixCutoff(datetime(2020, 1, 1), 10),
    )
    with pytest.raises(ValueError, match="inside"):
        V.validate_prefix_invariance(
            [original], [original, later], prefix_cutoff=R.PrefixCutoff(datetime(2020, 1, 1), 11),
        )


def test_scripts_have_no_runtime_or_result_surface() -> None:
    paths = [ROOT / path for path in V.ALLOWED_C2_FILES if path.startswith("scripts/")]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for forbidden in ("argparse", "metatrader", "order_send", "account_login", "--live", "--demo"):
        assert forbidden not in text


def test_scripts_structurally_forbid_writes_subprocesses_and_neighbor_evidence_paths() -> None:
    paths = [ROOT / path for path in V.ALLOWED_C2_FILES if path.startswith("scripts/")]
    forbidden_imports = {"argparse", "subprocess", "MetaTrader5", "requests"}
    forbidden_calls = {"open", "exec", "eval", "compile", "system", "popen", "run", "call", "check_call", "check_output"}
    forbidden_methods = {"write_text", "write_bytes", "touch", "mkdir", "unlink", "rename", "to_csv", "to_json", "to_parquet"}
    forbidden_path_tokens = ("portfolio_trades.csv", "h4_trades.csv", "h4_positions.csv", "h4_exposure.csv", "drawdown.csv", "pnl.csv")
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
                assert not forbidden_imports.intersection(modules)
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                assert name not in forbidden_calls
                assert name not in forbidden_methods
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not any(token in node.value.lower() for token in forbidden_path_tokens)
        assert not any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and "__name__" in ast.unparse(node.test) for node in ast.walk(tree))


def test_c3_input_manifest_validation_is_hash_and_size_exact() -> None:
    content = b'{"market_only":true}'
    manifest = {"inputs": {"market.json": {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}}}
    V.validate_c3_input_manifest(manifest, {"market.json": content})
    with pytest.raises(ValueError, match="hash"):
        V.validate_c3_input_manifest(manifest, {"market.json": content + b" "})
