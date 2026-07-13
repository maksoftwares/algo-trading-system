from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from ml.a3_meta_v1.historical_backtest_training import train_historical_backtest_model


def _write_source(root: Path, name: str, split: str, start_year: int) -> str:
    source_dir = root / "fixtures" / f"{name}_{split}"
    source_dir.mkdir(parents=True)
    signals = source_dir / "signals.csv"
    trades = source_dir / "trades.csv"
    summary = source_dir / "summary.json"
    direction = "LONG" if name.startswith("long") else "SHORT"

    signal_fields = [
        "timestamp_broker",
        "stage",
        "direction",
        "spread_points",
        "recent_high",
        "recent_low",
        "atr",
        "body_fraction",
        "close_location",
        "three_bar_move_atr",
        "break_distance_atr",
        "estimated_cost_r",
    ]
    trade_fields = ["entry_time", "direction", "profit_aed"]
    signal_rows = []
    trade_rows = []
    for index in range(6):
        timestamp = f"{start_year}.01.{index + 1:02d} {8 + index:02d}:00:00"
        signal_rows.append(
            {
                "timestamp_broker": timestamp,
                "stage": "WOULD_SIGNAL",
                "direction": direction,
                "spread_points": 20 + index,
                "recent_high": 1902 + index,
                "recent_low": 1898 + index,
                "atr": 2.0,
                "body_fraction": 0.4 + index / 20,
                "close_location": 0.8 if direction == "LONG" else 0.2,
                "three_bar_move_atr": 0.5 if direction == "LONG" else -0.5,
                "break_distance_atr": 0.3 + index / 20,
                "estimated_cost_r": 0.05,
            }
        )
        trade_rows.append(
            {"entry_time": timestamp, "direction": direction, "profit_aed": 5.0 if index % 2 else -3.0}
        )
    with signals.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=signal_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(signal_rows)
    with trades.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trade_fields)
        writer.writeheader()
        writer.writerows(trade_rows)
    summary.write_text(
        json.dumps(
            {
                "name": name,
                "signal_csv": str(signals),
                "trade_csv": str(trades),
                "mt5_report_metrics": {"History Quality": "99%"},
            }
        ),
        encoding="utf-8",
    )
    return str(summary.relative_to(root))


def _contract(root: Path, validation_year: int = 2022) -> Path:
    sources = []
    for split, year in (("train", 2021), ("validation", validation_year)):
        for name in ("long_family", "short_family"):
            sources.append(
                {
                    "split": split,
                    "strategy_family": name,
                    "summary_json": _write_source(root, name, split, year),
                }
            )
    payload = {
        "schema_version": "a3_ml_historical_backtest_training_v1",
        "symbol": "XAUUSD",
        "model_family": "LOGISTIC_REGRESSION_V1",
        "random_seed": 7,
        "decision_threshold": 0.5,
        "minimum_train_rows": 10,
        "minimum_validation_rows": 10,
        "minimum_history_quality_pct": 98,
        "train_end": "2021-12-31T23:59:59Z",
        "validation_start": "2022-01-01T00:00:00Z",
        "sources": sources,
        "outputs": {
            "dataset_csv": "outputs/dataset.csv",
            "model_json": "outputs/model.json",
            "status_json": "outputs/status.json",
            "model_card_md": "outputs/model_card.md",
        },
        "research_only": True,
        "python_demo_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    path = root / "contract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_trains_with_strict_out_of_time_split(tmp_path: Path) -> None:
    status_path = train_historical_backtest_model(tmp_path, _contract(tmp_path))
    status = json.loads(status_path.read_text(encoding="utf-8"))

    assert status["status"] == "TRAINED_RESEARCH_ONLY"
    assert status["training_population"]["rows"] == 12
    assert status["validation_population"]["rows"] == 12
    assert status["authorization"]["broker_action_authorized"] is False
    assert Path(status["artifacts"]["model_json"]).exists()


def test_rejects_validation_rows_before_contract_start(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="validation split contains rows before validation_start"):
        train_historical_backtest_model(tmp_path, _contract(tmp_path, validation_year=2021))
