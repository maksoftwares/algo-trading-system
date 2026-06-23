from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from phase2x_test_helpers import load_script


def test_c01_pipeline_builds_scoped_snapshot_and_abstains_when_pipeline_only(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    _write_decisions(decisions, _decision_rows(6) + [_non_raw_row(), _non_xau_row()])
    _write_trades(trades, [_trade_row(_decision_rows(1)[0]["signal_id"], cost_r="0.12")])
    _write_m5_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )

    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)
    feature_matrix = _read_csv(output.feature_matrix_csv)
    scores = _read_csv(output.offline_scores_csv)

    assert output.status == "PIPELINE_ONLY"
    assert audit["scope"]["account_scopes"] == ["1025742", "1033030", "1033669"]
    assert audit["raw_source_row_counts"]["scoped_raw_rows"] == 6
    assert audit["raw_source_row_counts"]["rejected_rows"] == 2
    assert audit["per_account_counts"]["1033669"]["snapshot_rows"] == 6
    assert audit["per_account_counts"]["1025742"]["snapshot_rows"] == 0
    assert audit["per_account_counts"]["1033030"]["snapshot_rows"] == 0
    assert audit["labeled_and_trainable_setup_groups"]["candidate_trainable_groups"] == 0
    assert "does not touch MT5 runtime" in audit["authority"]
    assert {row["symbol"] for row in snapshot} == {"XAUUSD"}
    assert {row["candidate_id"] for row in snapshot} == {"B0_RAW_ALL_SESSION"}
    assert "False" in {row["opened"] for row in snapshot}
    assert all(row["action"] == "ABSTAIN" for row in scores)
    assert all(row["dataset_status"] == "PIPELINE_ONLY" for row in scores)
    assert {row["account_scope"] for row in scores} == {"1033669"}
    assert feature_matrix[0]["account_scope"] == "1033669"
    assert "y_net_R_expected" not in feature_matrix[0]
    assert "final_r_if_raw" not in feature_matrix[0]


def test_c01_pipeline_accepts_all_three_account_scopes(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    rows = (
        _decision_rows(2, account="1025742", start_minute=20)
        + _decision_rows(2, account="1033030", start_minute=25)
        + _decision_rows(2, account="1033669", start_minute=30)
    )
    _write_decisions(decisions, rows)
    _write_trades(trades, [])
    _write_m5_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )

    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    snapshot = _read_csv(output.snapshot_csv)
    matrix = _read_csv(output.feature_matrix_csv)

    assert audit["raw_source_row_counts"]["scoped_raw_rows"] == 6
    assert audit["per_account_counts"]["1025742"]["snapshot_rows"] == 2
    assert audit["per_account_counts"]["1033030"]["snapshot_rows"] == 2
    assert audit["per_account_counts"]["1033669"]["snapshot_rows"] == 2
    assert {row["account_scope"] for row in snapshot} == {"1025742", "1033030", "1033669"}
    assert {row["account_scope"] for row in matrix} == {"1025742", "1033030", "1033669"}
    assert len({row["setup_group_id"] for row in snapshot}) == 6


def test_c01_pipeline_fails_closed_on_row_time_leakage(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    row = _decision_rows(1)[0]
    row["decision_time"] = "2026-06-01 06:39:00"
    _write_decisions(decisions, [row])
    _write_trades(trades, [])
    _write_m5_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )
    audit = json.loads(output.data_audit_json.read_text(encoding="utf-8"))
    scores = _read_csv(output.offline_scores_csv)

    assert output.status == "DATA_LEAKAGE_FAIL"
    assert len(audit["leakage_violations"]) == 1
    assert scores[0]["action"] == "ABSTAIN"
    assert scores[0]["reason"] == "DATA_LEAKAGE_FAIL"


def test_c01_pipeline_uses_decision_time_cost_only(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c01_pipeline")
    root = tmp_path / "phase1"
    decisions = root / "outputs" / "reports" / "decisions.csv"
    trades = root / "outputs" / "reports" / "trades.csv"
    bars_dir = root / "outputs" / "reports" / "bars"
    rows = _decision_rows(2)
    rows[1]["estimated_total_cost_R"] = "0.077"
    _write_decisions(decisions, rows)
    _write_trades(trades, [_trade_row(rows[0]["signal_id"], cost_r="0.31")])
    _write_m5_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=decisions,
        trades_csv=trades,
        bars_dir=bars_dir,
        data_audit_json=root / "outputs" / "reports" / "audit.json",
    )

    matrix = _read_csv(output.feature_matrix_csv)
    assert matrix[0]["cost_R"] == ""
    assert matrix[0]["cost_R__missing"] == "1"
    assert matrix[1]["cost_R"] == "0.077"
    assert matrix[1]["cost_R__missing"] == "0"


def _decision_rows(count: int, *, account: str = "1033669", start_minute: int = 20) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    base = datetime(2026, 6, 1, 6, start_minute)
    for index in range(count):
        break_time = base + timedelta(minutes=index * 20)
        retest_time = break_time + timedelta(minutes=10)
        confirmation_time = retest_time + timedelta(minutes=5)
        decision_time = confirmation_time + timedelta(minutes=5)
        direction = "LONG" if index % 2 == 0 else "SHORT"
        rows.append(
            {
                "signal_id": (
                    f"{account}|XAUUSD|breakout_retest|{direction}|"
                    f"{_dt(break_time)}|{_dt(retest_time)}|{_dt(confirmation_time)}|4500.{index:02d}"
                ),
                "candidate_id": "B0_RAW_ALL_SESSION",
                "decision_time": _dt(decision_time),
                "direction": direction,
                "keep": "True",
                "opened": "True" if index % 3 else "False",
                "reason": "KEEP_RAW" if index % 3 else "VIRTUAL_POSITION_ALREADY_OPEN",
                "session_bucket": "Morning 06:00-11:59",
                "h1_regime": "DATA_UNAVAILABLE",
                "final_r_if_raw": "1.5" if index % 2 == 0 else "-1.0",
                "estimated_total_cost_R": "",
            }
        )
    return rows


def _non_raw_row() -> dict[str, str]:
    row = _decision_rows(1)[0]
    row["candidate_id"] = "A3_SQ_COMBINED_V1"
    return row


def _non_xau_row() -> dict[str, str]:
    row = _decision_rows(1)[0]
    row["signal_id"] = row["signal_id"].replace("XAUUSD", "EURUSD")
    return row


def _trade_row(signal_id: str, *, cost_r: str) -> dict[str, str]:
    return {
        "signal_id": signal_id,
        "candidate_id": "B0_RAW_ALL_SESSION",
        "outcome": "WIN",
        "cost_r": cost_r,
        "loss_class": "WIN",
        "exit_time": "2026-06-01 07:10:00",
    }


def _write_decisions(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "signal_id",
        "candidate_id",
        "decision_time",
        "direction",
        "keep",
        "opened",
        "reason",
        "session_bucket",
        "h1_regime",
        "final_r_if_raw",
        "estimated_total_cost_R",
    ]
    _write_csv(path, fields, rows)


def _write_trades(path: Path, rows: list[dict[str, str]]) -> None:
    _write_csv(path, ["signal_id", "candidate_id", "outcome", "cost_r", "loss_class", "exit_time"], rows)


def _write_m5_bars(path: Path) -> None:
    start = datetime(2026, 6, 1, 0, 0)
    rows = []
    price = 4500.0
    for index in range(160):
        bar_start = start + timedelta(minutes=5 * index)
        bar_end = bar_start + timedelta(minutes=5)
        open_price = price + index * 0.10
        close = open_price + (0.30 if index % 2 == 0 else -0.20)
        rows.append(
            {
                "bar_start_utc": _dt(bar_start),
                "bar_end_utc": _dt(bar_end),
                "open": f"{open_price:.2f}",
                "high": f"{max(open_price, close) + 0.50:.2f}",
                "low": f"{min(open_price, close) - 0.50:.2f}",
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


def _dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")
