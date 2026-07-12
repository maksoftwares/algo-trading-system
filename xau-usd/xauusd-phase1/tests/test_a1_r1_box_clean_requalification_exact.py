from __future__ import annotations

import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r1_box_clean_requalification_exact as runner  # noqa: E402


def test_clean_r1_variant_is_single_unmasked_strict_router_cell() -> None:
    variants = runner.build_variants()
    checks = runner.static_checks(variants)
    assert len(variants) == 1
    assert all(checks.values()), checks
    inputs = variants[0].tester_inputs
    assert inputs["InpRegimeRouterMode"] == "1"
    assert inputs["InpH4D1PrevMonthHealthGateEnabled"] == "false"
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    assert inputs["InpBlockedLongEntryHoursCsv"] == ""
    assert inputs["InpBlockedShortEntryHoursCsv"] == ""
    assert inputs["InpUseDirectionalSessionFilter"] == "false"


def test_mt5_drawdown_parser_uses_relative_percentage_field() -> None:
    parsed = runner.mt5_drawdown(
        {
            "Balance Drawdown Maximal": "866.37 (12.71%)",
            "Equity Drawdown Maximal": "1 733.37 (24.59%)",
            "Balance Drawdown Relative": "16.44% (1 104.54)",
            "Equity Drawdown Relative": "31.06% (2 185.72)",
        }
    )
    assert parsed["balance_dd_maximal_usd"] == 866.37
    assert parsed["equity_dd_maximal_usd"] == 1733.37
    assert parsed["balance_dd_relative_pct"] == 16.44
    assert parsed["equity_dd_relative_pct"] == 31.06


def test_episode_definition_requires_an_inactive_calendar_month() -> None:
    rows = [
        {"entry_date": date(2023, 1, 3), "pnl_usd": 10.0},
        {"entry_date": date(2023, 2, 3), "pnl_usd": -2.0},
        {"entry_date": date(2023, 4, 3), "pnl_usd": 5.0},
        {"entry_date": date(2023, 7, 3), "pnl_usd": 7.0},
    ]
    episodes = runner.episode_rows(rows)
    assert [(row["start_month"], row["end_month"]) for row in episodes] == [
        ("2023-01", "2023-02"),
        ("2023-04", "2023-04"),
        ("2023-07", "2023-07"),
    ]
    assert [row["net"] for row in episodes] == [8.0, 5.0, 7.0]


def test_preregistration_and_both_frozen_windows_exist() -> None:
    assert runner.PREREG.exists()
    assert [window["name"] for window in runner.WINDOWS] == [
        "primary_202207_202606",
        "prehistory_201601_202112",
    ]
