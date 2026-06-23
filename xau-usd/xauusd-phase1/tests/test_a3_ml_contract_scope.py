from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_contract_scope_defaults_to_breakout_only_when_no_approval(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_scope import load_contract_scope

    scope = load_contract_scope(tmp_path)

    assert scope.contract_expansion_authorized is False
    assert scope.active_families == ("breakout_retest",)
    assert scope.scope_name == "breakout_retest_only"


def test_contract_scope_requires_review_reference_when_authorized(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_scope import load_contract_scope

    _write_json(
        tmp_path / "config" / "ml" / "a3_ml_contract_expansion.json",
        {
            "schema_version": "a3_ml_contract_expansion_v1",
            "contract_expansion_authorized": True,
            "review_reference": "",
            "allowed_families": ["round_number_retest"],
            "accounts": {},
        },
    )

    try:
        load_contract_scope(tmp_path)
    except ValueError as exc:
        assert "review_reference" in str(exc)
    else:
        raise AssertionError("authorized contract expansion accepted without review_reference")


def test_family_normalization_prefers_known_candidate_and_uses_catalog_fallback() -> None:
    from ml.a3_meta_v1.contract_scope import normalize_family_name

    assert normalize_family_name("round_number_retest", "A3_BREAKOUT_PLAIN", "breakout_retest") == "round_number_retest"
    assert normalize_family_name("", "A3_BREAKOUT_PLAIN", "breakout_retest") == "breakout_retest"


def test_history_snapshot_catalog_overlay_is_approval_gated(tmp_path: Path) -> None:
    from ml.a3_meta_v1.history_log_snapshot import _catalog_entries_for_account

    root = tmp_path / "phase1"
    catalog = root / "config" / "ml" / "log_catalog_a1.yaml"
    _write_json(
        catalog,
        {
            "schema_version": "c02_log_catalog_v1",
            "account_label": "A1",
            "entries": [_catalog_entry("a1_breakout", "breakout.csv", "breakout_retest")],
        },
    )

    assert [entry["logical_source_name"] for entry in _catalog_entries_for_account(root, "A1", catalog)] == [
        "a1_breakout"
    ]

    _write_json(
        root / "config" / "ml" / "a3_ml_contract_expansion.json",
        {
            "schema_version": "a3_ml_contract_expansion_v1",
            "contract_expansion_authorized": True,
            "review_reference": "C35 reviewer approved round_number_retest on 2026-06-22",
            "allowed_families": ["round_number_retest"],
            "accounts": {
                "A1": {
                    "entries": [
                        _catalog_entry(
                            "a1_round",
                            "experimental_demo_executor_signal_log_round_number_retest_v0_xauusd.csv",
                            "round_number_retest",
                        )
                    ]
                }
            },
        },
    )

    entries = _catalog_entries_for_account(root, "A1", catalog)

    assert [entry["logical_source_name"] for entry in entries] == ["a1_breakout", "a1_round"]
    assert entries[1]["family"] == "round_number_retest"


def test_c02_normalization_keeps_locked_family_until_expansion_is_approved(tmp_path: Path) -> None:
    from ml.a3_meta_v1.source_normalization import normalize_c02_snapshot

    root = _normalization_root(tmp_path)

    output = normalize_c02_snapshot(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    decisions = _read_csv(root / "outputs" / "reports" / "C02_NORMALIZED_DECISIONS.csv")

    assert payload["contract_scope"]["scope_name"] == "breakout_retest_only"
    assert len(decisions) == 1
    assert decisions[0]["signal_id"].split("|")[2] == "breakout_retest"

    _write_json(
        root / "config" / "ml" / "a3_ml_contract_expansion.json",
        {
            "schema_version": "a3_ml_contract_expansion_v1",
            "contract_expansion_authorized": True,
            "review_reference": "C35 reviewer approved round_number_retest on 2026-06-22",
            "allowed_families": ["round_number_retest"],
            "accounts": {},
        },
    )

    output = normalize_c02_snapshot(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    decisions = _read_csv(root / "outputs" / "reports" / "C02_NORMALIZED_DECISIONS.csv")

    assert payload["contract_scope"]["scope_name"] == "reviewer_approved_multi_family"
    assert {row["signal_id"].split("|")[2] for row in decisions} == {"breakout_retest", "round_number_retest"}
    assert payload["boundary"]["model_training_authorized"] is False


def test_c01_accepts_approved_family_scope_without_authorizing_training(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    _write_decisions(
        decisions,
        [
            _decision_row("breakout_retest", 0),
            _decision_row("round_number_retest", 1),
        ],
    )
    _write_csv(trades, ["signal_id", "candidate_id", "outcome", "cost_r", "loss_class", "exit_time"], [])
    _write_c01_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)

    assert audit["scope"]["contract_scope"] == "breakout_retest_only"
    assert audit["raw_source_row_counts"]["scoped_raw_rows"] == 1
    assert {row["base_family"] for row in snapshot} == {"breakout_retest"}

    _write_json(
        root / "config" / "ml" / "a3_ml_contract_expansion.json",
        {
            "schema_version": "a3_ml_contract_expansion_v1",
            "contract_expansion_authorized": True,
            "review_reference": "C35 reviewer approved round_number_retest on 2026-06-22",
            "allowed_families": ["round_number_retest"],
            "accounts": {},
        },
    )

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)

    assert audit["scope"]["contract_expansion_authorized"] is True
    assert audit["raw_source_row_counts"]["scoped_raw_rows"] == 2
    assert {row["base_family"] for row in snapshot} == {"breakout_retest", "round_number_retest"}
    assert audit["training_decision"]["supervised_training_allowed"] is False


def _normalization_root(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    dataset = root / "data" / "ml" / "a3_meta_v1" / "c02" / "TEST"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST", "output_root": str(dataset)})
    signal_log = dataset / "raw" / "A1" / "logs" / "mixed" / "mixed_signal_log.csv"
    _write_csv(
        signal_log,
        [
            "timestamp_utc",
            "symbol",
            "candidate",
            "direction",
            "would_signal",
            "level_price",
            "entry_price",
            "stop_loss",
            "take_profit",
            "stop_distance_points",
            "spread_points",
        ],
        [
            _signal_row("breakout_retest", "2026-06-01 06:20:00", "LONG", "4500.00"),
            _signal_row("round_number_retest", "2026-06-01 06:25:00", "SHORT", "4501.00"),
        ],
    )
    _write_json(
        dataset / "raw" / "A1" / "manifest" / "HISTORY_LOG_MANIFEST.json",
        {
            "account_label": "A1",
            "account_scope": "1025742",
            "log_records": [
                {
                    "source_type": "experimental_executor_signal_log",
                    "logical_source_name": "mixed_signal",
                    "family": "breakout_retest",
                    "filename": "mixed_signal_log.csv",
                    "snapshot_path": str(signal_log),
                    "sha256": "abc",
                }
            ],
        },
    )
    for timeframe in ("M5", "H1", "D1"):
        _write_raw_bars(dataset / "raw" / "A1" / "bars" / f"XAUUSD_{timeframe}.csv")
    return root


def _catalog_entry(logical_source_name: str, filename: str, family: str) -> dict[str, object]:
    return {
        "logical_source_name": logical_source_name,
        "source_type": "experimental_executor_signal_log",
        "filename": filename,
        "schema_version": "csv_runtime_log_v1",
        "family": family,
        "append_active": False,
    }


def _signal_row(candidate: str, timestamp: str, direction: str, price: str) -> dict[str, str]:
    return {
        "timestamp_utc": timestamp,
        "symbol": "XAUUSD",
        "candidate": candidate,
        "direction": direction,
        "would_signal": "true",
        "level_price": price,
        "entry_price": price,
        "stop_loss": "4490.00",
        "take_profit": "4515.00",
        "stop_distance_points": "300",
        "spread_points": "50",
    }


def _decision_row(family: str, offset: int) -> dict[str, str]:
    break_time = datetime(2026, 6, 1, 6, 0) + timedelta(minutes=offset * 20)
    retest_time = break_time + timedelta(minutes=10)
    confirmation_time = retest_time + timedelta(minutes=5)
    decision_time = confirmation_time + timedelta(minutes=5)
    direction = "LONG" if offset % 2 == 0 else "SHORT"
    return {
        "signal_id": (
            f"1033669|XAUUSD|{family}|{direction}|"
            f"{_dt(break_time)}|{_dt(retest_time)}|{_dt(confirmation_time)}|4500.{offset:02d}"
        ),
        "candidate_id": "B0_RAW_ALL_SESSION",
        "decision_time": _dt(decision_time),
        "direction": direction,
        "opened": "false",
        "reason": "TEST",
        "session_bucket": "Morning 06:00-11:59",
        "final_r_if_raw": "1.5" if direction == "LONG" else "-1.0",
        "estimated_total_cost_R": "",
    }


def _write_raw_bars(path: Path) -> None:
    rows = []
    for index in range(6):
        rows.append(
            {
                "time_utc": (datetime(2026, 6, 1, 0, 0) + timedelta(minutes=5 * index)).isoformat() + "Z",
                "open": "4500",
                "high": "4501",
                "low": "4499",
                "close": "4500.5",
                "tick_volume": "100",
                "spread": "50",
            }
        )
    _write_csv(path, ["time_utc", "open", "high", "low", "close", "tick_volume", "spread"], rows)


def _write_c01_bars(path: Path) -> None:
    rows = []
    for index in range(120):
        start = datetime(2026, 6, 1, 0, 0) + timedelta(minutes=5 * index)
        rows.append(
            {
                "bar_start_utc": _dt(start),
                "bar_end_utc": _dt(start + timedelta(minutes=5)),
                "open": "4500",
                "high": "4501",
                "low": "4499",
                "close": "4500.5",
                "tick_volume": "100",
                "spread": "50",
            }
        )
    _write_csv(path, ["bar_start_utc", "bar_end_utc", "open", "high", "low", "close", "tick_volume", "spread"], rows)


def _write_decisions(path: Path, rows: list[dict[str, str]]) -> None:
    _write_csv(
        path,
        [
            "signal_id",
            "candidate_id",
            "decision_time",
            "direction",
            "opened",
            "reason",
            "session_bucket",
            "final_r_if_raw",
            "estimated_total_cost_R",
        ],
        rows,
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")
