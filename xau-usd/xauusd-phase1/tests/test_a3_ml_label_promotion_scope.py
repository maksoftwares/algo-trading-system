from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_label_promotion_defaults_to_locked_scope(tmp_path: Path) -> None:
    from ml.a3_meta_v1.label_promotion_scope import load_label_promotion_scope

    scope = load_label_promotion_scope(tmp_path)

    assert scope.label_promotion_authorized is False
    assert scope.scope_name == "label_promotion_locked"
    assert scope.promotion_active("ADEQUATE") is False


def test_label_promotion_requires_review_reference_when_authorized(tmp_path: Path) -> None:
    from ml.a3_meta_v1.label_promotion_scope import load_label_promotion_scope

    _write_json(
        tmp_path / "config" / "ml" / "a3_ml_label_promotion.json",
        {
            "schema_version": "a3_ml_label_promotion_v1",
            "label_promotion_authorized": True,
            "review_reference": "",
            "allowed_label_statuses": ["TP", "SL"],
            "minimum_mature_labels": 300,
            "minimum_minority_labels": 90,
            "require_slippage_adequate": True,
        },
    )

    try:
        load_label_promotion_scope(tmp_path)
    except ValueError as exc:
        assert "review_reference" in str(exc)
    else:
        raise AssertionError("authorized label promotion accepted without review_reference")


def test_c01_keeps_source_labels_diagnostic_until_promotion_is_approved(tmp_path: Path) -> None:
    output = _run_c01(tmp_path, _decision_rows(["TP", "SL"]))
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)

    assert audit["label_promotion_scope"]["scope_name"] == "label_promotion_locked"
    assert audit["label_promotion_scope"]["promotion_active"] is False
    assert {row["label_status"] for row in snapshot} == {"OPTIMISTIC_DIAGNOSTIC_ONLY"}
    assert {row["candidate_trainable"] for row in snapshot} == {"false"}


def test_c01_promotes_reviewed_source_labels_when_slippage_gate_is_disabled(tmp_path: Path) -> None:
    root = tmp_path / "phase1"
    _write_label_promotion_config(root, require_slippage_adequate=False)

    output = _run_c01(tmp_path, _decision_rows(["TP", "SL"]))
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)

    assert audit["label_promotion_scope"]["scope_name"] == "reviewer_approved_label_promotion"
    assert audit["label_promotion_scope"]["promotion_active"] is True
    assert audit["label_promotion_scope"]["slippage_model_status"] == "INSUFFICIENT"
    assert {row["label_status"] for row in snapshot} == {"TP", "SL"}
    assert {row["candidate_trainable"] for row in snapshot} == {"true"}
    assert {row["row_status"] for row in snapshot} == {"REVIEWER_PROMOTED_TRAINABLE_ROW"}


def test_c01_blocks_approved_label_promotion_when_slippage_gate_is_required(tmp_path: Path) -> None:
    root = tmp_path / "phase1"
    _write_label_promotion_config(root, require_slippage_adequate=True)

    output = _run_c01(tmp_path, _decision_rows(["TP", "SL"]))
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)

    assert audit["label_promotion_scope"]["label_promotion_authorized"] is True
    assert audit["label_promotion_scope"]["promotion_active"] is False
    assert {row["label_status"] for row in snapshot} == {"OPTIMISTIC_DIAGNOSTIC_ONLY"}
    assert {row["candidate_trainable"] for row in snapshot} == {"false"}
    assert {row["row_status"] for row in snapshot} == {"PROMOTION_BLOCKED_SLIPPAGE"}


def _run_c01(tmp_path: Path, rows: list[dict[str, str]]):
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    _write_decisions(decisions, rows)
    _write_csv(trades, ["signal_id", "candidate_id", "outcome", "cost_r", "loss_class", "exit_time"], [])
    _write_m5_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")
    return module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )


def _write_label_promotion_config(root: Path, *, require_slippage_adequate: bool) -> None:
    _write_json(
        root / "config" / "ml" / "a3_ml_label_promotion.json",
        {
            "schema_version": "a3_ml_label_promotion_v1",
            "label_promotion_authorized": True,
            "review_reference": "C38 reviewer approved diagnostic label promotion on 2026-06-22",
            "allowed_label_statuses": ["TP", "SL"],
            "minimum_mature_labels": 300,
            "minimum_minority_labels": 90,
            "require_slippage_adequate": require_slippage_adequate,
        },
    )


def _decision_rows(label_statuses: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    base = datetime(2026, 6, 1, 6, 20)
    for index, label_status in enumerate(label_statuses):
        break_time = base + timedelta(minutes=index * 20)
        retest_time = break_time + timedelta(minutes=10)
        confirmation_time = retest_time + timedelta(minutes=5)
        decision_time = confirmation_time + timedelta(minutes=5)
        direction = "LONG" if label_status == "TP" else "SHORT"
        rows.append(
            {
                "signal_id": (
                    f"1033669|XAUUSD|breakout_retest|{direction}|"
                    f"{_dt(break_time)}|{_dt(retest_time)}|{_dt(confirmation_time)}|4500.{index:02d}"
                ),
                "candidate_id": "B0_RAW_ALL_SESSION",
                "decision_time": _dt(decision_time),
                "direction": direction,
                "opened": "true",
                "reason": "KEEP_RAW",
                "session_bucket": "Morning 06:00-11:59",
                "label_status": label_status,
                "final_r_if_raw": "1.5" if label_status == "TP" else "-1.0",
                "estimated_total_cost_R": "",
            }
        )
    return rows


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
            "label_status",
            "final_r_if_raw",
            "estimated_total_cost_R",
        ],
        rows,
    )


def _write_m5_bars(path: Path) -> None:
    start = datetime(2026, 6, 1, 0, 0)
    rows = []
    for index in range(160):
        bar_start = start + timedelta(minutes=5 * index)
        close = 4500.0 + index * 0.10
        rows.append(
            {
                "bar_start_utc": _dt(bar_start),
                "bar_end_utc": _dt(bar_start + timedelta(minutes=5)),
                "open": f"{close - 0.10:.2f}",
                "high": f"{close + 0.50:.2f}",
                "low": f"{close - 0.50:.2f}",
                "close": f"{close:.2f}",
                "tick_volume": str(1000 + index),
                "spread": "50",
                "real_volume": "0",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "source_terminal": "fixture",
            }
        )
    _write_csv(
        path,
        [
            "bar_start_utc",
            "bar_end_utc",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread",
            "real_volume",
            "symbol",
            "timeframe",
            "source_terminal",
        ],
        rows,
    )


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
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
