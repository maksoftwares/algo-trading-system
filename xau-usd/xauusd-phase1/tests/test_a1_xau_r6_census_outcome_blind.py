from __future__ import annotations

import json
import sys
import ast
import hashlib
import dataclasses
from datetime import datetime, timedelta
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
    tick_content = b'{"sequence":100}\n'
    payloads = {
        "A1_XAU_R6_C3_BARS_CONTRACT.json": content,
        "A1_XAU_R6_C3_TICKS.ndjson": tick_content,
    }
    manifest = {
        "schema_version": "a1_xau_r6_c3_input_manifest_v1",
        "generator": {"commit": "a" * 40, "tree": "b" * 40},
        "timestamp_basis": "BROKER_SERVER_WALL_CLOCK",
        "warmup": {
            "h1_bars": 30, "h4_bars": 70, "d1_bars": 277,
            "from_inclusive": "2015-06-01T00:00:00", "decision_from_inclusive": "2016-07-01T00:00:00",
        },
        "data": {
            "from_inclusive": "2016-07-01T00:00:00", "to_exclusive": "2026-07-01T00:00:00",
            "h1_bar_count": 60000, "h4_bar_count": 15000, "d1_bar_count": 2600,
            "h1_gap_count": 0, "h4_gap_count": 0, "d1_gap_count": 0,
        },
        "tick_stream": {
            "format": "ndjson_utf8", "count": 10, "first_sequence": 100, "last_sequence": 109,
            "gap_count": 0, "session_open_required": True, "source_h1_bar_time_required": True,
            "first_time": "2016-07-01T00:00:00", "last_time": "2026-07-01T00:00:00",
        },
        "contract_identity": {
            "server": "Capital.ComMena-Demo", "symbol": "XAUUSD", "account_currency": "USD",
            "snapshot_sha256": "c" * 64,
        },
        "inputs": {
            name: {"sha256": hashlib.sha256(value).hexdigest(), "size_bytes": len(value)}
            for name, value in payloads.items()
        },
    }
    V.validate_c3_input_manifest(manifest, content)
    with pytest.raises(ValueError, match="hash"):
        V.validate_c3_input_manifest(manifest, content + b" ")
    bad = json.loads(json.dumps(manifest))
    bad["tick_stream"]["gap_count"] = 1
    with pytest.raises(ValueError, match="completeness"):
        V.validate_c3_input_manifest(bad, content)


def test_reviewed_c3_runner_streams_ticks_and_builds_canonical_package() -> None:
    contract = R.Contract(
        account_currency="USD", account_leverage=50, margin_mode=2,
        server="Capital.ComMena-Demo", symbol="XAUUSD", point=0.01, digits=2,
        tick_size=0.01, tick_value=1.0, tick_value_loss=1.0,
        volume_min=0.01, volume_step=0.01, volume_max=1000.0,
        contract_size=100.0, stops_level=0, freeze_level=0,
    )

    def bars(count: int, spacing: timedelta) -> list[dict[str, object]]:
        start = R.FROM_INCLUSIVE - spacing * count
        rows = [
            {"time": (start + spacing * index).isoformat(), "open": 100, "high": 101, "low": 99, "close": 100.5}
            for index in range(count)
        ]
        rows.append({"time": R.TO_EXCLUSIVE.isoformat(), "open": 100, "high": 101, "low": 99, "close": 100.5})
        return rows

    market = {
        "h1": bars(25, timedelta(hours=1)), "h4": bars(61, timedelta(hours=4)),
        "d1": bars(277, timedelta(days=1)), "contract": dataclasses.asdict(contract), "symbol": "XAUUSD",
    }
    bars_content = json.dumps(market, sort_keys=True, separators=(",", ":")).encode()
    tick_rows = [
        {"time": R.FROM_INCLUSIVE.isoformat(), "sequence": 100, "bid": 100, "ask": 100.01, "session_open": True, "source_h1_bar_time": R.FROM_INCLUSIVE.isoformat()},
        {"time": R.TO_EXCLUSIVE.isoformat(), "sequence": 101, "bid": 100, "ask": 100.01, "session_open": True, "source_h1_bar_time": R.TO_EXCLUSIVE.isoformat()},
    ]
    tick_lines = [(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in tick_rows]
    tick_content = b"".join(tick_lines)
    contract_sha = hashlib.sha256(
        json.dumps(dataclasses.asdict(contract), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest = {
        "schema_version": "a1_xau_r6_c3_input_manifest_v1",
        "generator": {"commit": "a" * 40, "tree": "b" * 40},
        "timestamp_basis": "BROKER_SERVER_WALL_CLOCK",
        "warmup": {
            "h1_bars": 25, "h4_bars": 61, "d1_bars": 277,
            "from_inclusive": market["d1"][0]["time"], "decision_from_inclusive": R.FROM_INCLUSIVE.isoformat(),
        },
        "data": {
            "from_inclusive": R.FROM_INCLUSIVE.isoformat(), "to_exclusive": R.TO_EXCLUSIVE.isoformat(),
            "h1_bar_count": len(market["h1"]), "h4_bar_count": len(market["h4"]), "d1_bar_count": len(market["d1"]),
            "h1_gap_count": 0, "h4_gap_count": 0, "d1_gap_count": 0,
        },
        "tick_stream": {
            "format": "ndjson_utf8", "count": 2, "first_sequence": 100, "last_sequence": 101,
            "gap_count": 0, "session_open_required": True, "source_h1_bar_time_required": True,
            "first_time": R.FROM_INCLUSIVE.isoformat(), "last_time": R.TO_EXCLUSIVE.isoformat(),
        },
        "contract_identity": {
            "server": contract.server, "symbol": contract.symbol, "account_currency": contract.account_currency,
            "snapshot_sha256": contract_sha,
        },
        "inputs": {
            "A1_XAU_R6_C3_BARS_CONTRACT.json": {"sha256": hashlib.sha256(bars_content).hexdigest(), "size_bytes": len(bars_content)},
            "A1_XAU_R6_C3_TICKS.ndjson": {"sha256": hashlib.sha256(tick_content).hexdigest(), "size_bytes": len(tick_content)},
        },
    }
    detection, package = V.run_c3_in_memory(
        manifest=manifest, bars_content=bars_content, tick_lines=iter(tick_lines), row_schema=schema(),
        rule_manifest_sha256="c" * 64,
    )
    assert not detection.rows
    assert set(package) == {
        "A1_XAU_R6_OUTCOME_BLIND_DETECTION.json", "A1_XAU_R6_OUTCOME_BLIND_ROWS.csv",
        "A1_XAU_R6_OUTCOME_BLIND_SUMMARY.md", "A1_XAU_R6_EVIDENCE_MANIFEST.json",
    }
    assert package["A1_XAU_R6_OUTCOME_BLIND_ROWS.csv"].startswith("schema_version,")
