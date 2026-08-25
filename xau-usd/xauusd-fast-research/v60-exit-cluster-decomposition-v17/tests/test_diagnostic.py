from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v17_diagnostic", ROOT / "run_diagnostic.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_profit_factor_and_metrics() -> None:
    observed = module.metrics([2.0, -1.0, 3.0, -1.0])
    assert observed["trades"] == 4
    assert observed["wins"] == 2
    assert observed["net_pnl_usd"] == 3.0
    assert observed["profit_factor"] == 2.5
    assert observed["win_rate"] == 0.5


def test_assign_fold_is_left_closed_right_open() -> None:
    times = pd.Series(
        pd.to_datetime(
            ["2023-12-31T23:59:59Z", "2024-01-01T00:00:00Z", "2026-07-01T00:00:00Z"],
            utc=True,
        )
    )
    folds = [
        {"fold_id": "A", "start": "2021-01-01T00:00:00Z", "end": "2024-01-01T00:00:00Z"},
        {"fold_id": "B", "start": "2024-01-01T00:00:00Z", "end": "2026-07-01T00:00:00Z"},
    ]
    assert module.assign_fold(times, folds).tolist() == ["A", "B", "OUTSIDE"]


def test_cluster_annotations_require_resolved_prior_loss() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_id": "a",
                "source_id": "R4",
                "direction": "SHORT",
                "entry": "2026-07-28T10:00:00Z",
                "exit": "2026-07-28T11:00:00Z",
                "pnl": -5.0,
            },
            {
                "trade_id": "b",
                "source_id": "R4",
                "direction": "SHORT",
                "entry": "2026-07-28T10:30:00Z",
                "exit": "2026-07-28T12:00:00Z",
                "pnl": -4.0,
            },
            {
                "trade_id": "c",
                "source_id": "R4",
                "direction": "SHORT",
                "entry": "2026-07-28T11:30:00Z",
                "exit": "2026-07-28T13:00:00Z",
                "pnl": 3.0,
            },
        ]
    )
    observed = module.annotate_clusters(
        frame, entry_column="entry", exit_column="exit", pnl_column="pnl"
    ).set_index("trade_id")
    assert observed.loc["a", "cluster_size"] == 3
    assert not bool(observed.loc["a", "post_prior_loss_same_day"])
    assert not bool(observed.loc["b", "post_prior_loss_same_day"])
    assert bool(observed.loc["c", "post_prior_loss_same_day"])


def test_protection_eligibility_requires_two_negative_folds() -> None:
    rows = []
    for fold, delta in (("A", -1.0), ("B", -1.0), ("C", 1.0)):
        for index in range(10):
            rows.append(
                {
                    "source_id": "S",
                    "fold_id": fold,
                    "protection_delta_usd": delta,
                    "protection_changed": True,
                    "protection_action": True,
                    "pnl_changed": True,
                }
            )
    config = {
        "folds": [{"fold_id": value} for value in ("A", "B", "C")],
        "eligibility": {
            "minimum_cohort_trades": 30,
            "minimum_negative_historical_folds": 2,
        },
    }
    observed = module.eligible_protection_sources(pd.DataFrame(rows), config)
    assert observed[0]["eligible"] is True
    assert observed[0]["negative_historical_folds"] == 2
    assert observed[0]["protection_action_trades"] == 30


def test_protection_audit_accepts_mixed_iso_precision() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_id": "a",
                "source_id": "S",
                "specialist_id": "S",
                "sleeve_type": "CORE",
                "direction": "LONG",
                "risk_usd": 5.0,
                "open_cost_usd": 0.1,
                "entry_time_utc": "2021-01-01T00:00:00Z",
                "exit_time_utc": "2021-01-01T01:00:00.065000Z",
                "endpoint_exit_time_utc": "2021-01-01T01:00:00Z",
                "endpoint_pnl_usd": 2.0,
                "pnl_usd": 1.5,
                "close_reason": "OPEN_PROFIT_GIVEBACK",
            }
        ]
    )
    config = {
        "tolerance_usd": 1e-9,
        "folds": [
            {
                "fold_id": "A",
                "start": "2021-01-01T00:00:00Z",
                "end": "2022-01-01T00:00:00Z",
            }
        ],
    }
    audit, _, _, _ = module.protection_audit(frame, config)
    assert bool(audit.loc[0, "protection_changed"])
    assert bool(audit.loc[0, "protection_action"])
    assert bool(audit.loc[0, "pnl_changed"])
    assert audit.loc[0, "protection_delta_usd"] == -0.5


def test_timed_metrics_orders_drawdown_by_close_time() -> None:
    frame = pd.DataFrame(
        [
            {"trade_id": "late", "close": "2026-01-02T00:00:00Z", "pnl": 5.0},
            {"trade_id": "first", "close": "2026-01-01T00:00:00Z", "pnl": -3.0},
        ]
    )
    observed = module.timed_metrics(frame, pnl_column="pnl", close_column="close")
    assert observed["net_pnl_usd"] == 2.0
    assert observed["closed_drawdown_usd"] == 3.0
