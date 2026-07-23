from __future__ import annotations

import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.window_performance import build_window_report  # noqa: E402


def test_completed_window_metrics_reconcile() -> None:
    report = build_window_report()
    three = report["windows"]["3_months"]
    six = report["windows"]["6_months"]
    year = report["windows"]["1_year"]

    assert (three["trades"], three["wins"], three["losses"]) == (68, 38, 30)
    assert three["net_pnl_usd"] == 3.29
    assert three["profit_factor"] == 1.101
    assert (six["trades"], six["net_pnl_usd"], six["profit_factor"]) == (140, 11.43, 1.1502)
    assert (year["trades"], year["net_pnl_usd"], year["profit_factor"]) == (241, 16.03, 1.1194)
    assert report["basis"]["full_ledger_net_usd"] == 101.82
