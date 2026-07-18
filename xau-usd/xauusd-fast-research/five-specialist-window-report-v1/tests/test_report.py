from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("five_specialist_report", ROOT / "build_report.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError(ROOT / "build_report.py")
REPORT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPORT
SPEC.loader.exec_module(REPORT)


def _ledger() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_id": ["a", "b", "c"],
            "specialist_id": ["R1", "R2", "R2"],
            "entry_time_utc": pd.to_datetime(
                ["2026-01-01", "2026-01-01 12:00", "2026-01-03"],
                format="mixed",
                utc=True,
            ),
            "exit_time_utc": pd.to_datetime(
                ["2026-01-02", "2026-01-04", "2026-01-05"],
                format="mixed",
                utc=True,
            ),
            "pnl_usd_0p01_equiv": [10.0, -4.0, 8.0],
            "stress_net_r": [np.nan, -1.0, 2.0],
        }
    )


def test_summary_uses_realized_exit_order() -> None:
    result = REPORT.summarize(_ledger())
    assert result["trades"] == 3
    assert result["net_usd_0p01_equiv"] == 14.0
    assert result["profit_factor_usd"] == 4.5
    assert result["closed_drawdown_usd"] == 4.0
    assert np.isnan(result["net_stress_r"])


def test_concurrency_counts_cross_specialist_overlap() -> None:
    result = REPORT.concurrency_metrics(
        _ledger(), pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-02-01", tz="UTC")
    )
    assert result["maximum_concurrent_positions"] == 2
    assert result["entries_while_any_position_open"] == 2
    assert result["entries_while_other_specialist_open"] == 1
