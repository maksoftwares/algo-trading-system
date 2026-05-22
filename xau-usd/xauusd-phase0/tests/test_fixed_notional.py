from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ProjectConfig
from phase0.fixed_notional import _add_cost_r_fields, generate_fixed_notional_report


def test_add_cost_r_fields_uses_price_risk_and_actual_risk():
    frame = pd.DataFrame(
        [
            {
                "symbol": "XAUUSD",
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "metadata_spread_points": 20.0,
                "metadata_entry_slippage_price": 0.05,
                "metadata_exit_slippage_price": 0.03,
                "metadata_actual_risk_usd": 50.0,
                "costs_usd": 2.5,
                "r_multiple": 1.0,
            }
        ]
    )

    result = _add_cost_r_fields(frame)

    assert result["entry_spread_R"].iloc[0] == 0.2
    assert result["entry_slippage_R"].iloc[0] == 0.05
    assert result["exit_slippage_R"].iloc[0] == 0.03
    assert result["commission_R"].iloc[0] == 0.05
    assert result["all_in_cost_R"].iloc[0] == 0.33


def test_generate_fixed_notional_report_writes_outputs(tmp_path: Path):
    expert_dir = tmp_path / "outputs" / "matrix_results" / "breakout_retest"
    expert_dir.mkdir(parents=True)
    summary_path = expert_dir / "cell_1_breakout_retest_capital_com_median.csv"
    trades_path = expert_dir / "cell_1_breakout_retest_capital_com_median_trades.csv"
    summary_path.write_text(
        "expert,broker,cost_model,symbol,cell_id\n"
        "breakout_retest,capital_com,median,XAUUSD,1\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            _trade_row(1.5, 75.0, 0.0),
            _trade_row(-1.0, -50.0, 0.0),
            _trade_row(1.5, 75.0, 0.0),
        ]
    ).to_csv(trades_path, index=False)
    config = ProjectConfig(
        tmp_path,
        {"project": {"starting_equity_usd": 10000.0, "phase0_risk_per_trade_pct": 0.005}},
        {},
        {},
        {},
        {},
    )

    output = generate_fixed_notional_report(config, "breakout_retest")

    assert output.status == "PASS"
    assert output.trade_count == 3
    assert output.fixed_risk_usd == 50.0
    assert output.report_path.exists()
    assert output.summary_path.exists()
    assert output.manifest_path.exists()


def _trade_row(r_multiple: float, gross_pnl: float, costs: float) -> dict[str, object]:
    return {
        "expert": "breakout_retest",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "entry_time_utc": "2024-01-01T00:00:00+00:00",
        "exit_time_utc": "2024-01-01T00:05:00+00:00",
        "entry_price": 100.0,
        "exit_price": 101.0,
        "stop_loss": 99.0,
        "take_profit": 101.5,
        "lots": 0.5,
        "gross_pnl_usd": gross_pnl,
        "costs_usd": costs,
        "net_pnl_usd": gross_pnl - costs,
        "r_multiple": r_multiple,
        "exit_reason": "test",
        "metadata_spread_points": 20.0,
        "metadata_entry_slippage_price": 0.0,
        "metadata_exit_slippage_price": 0.0,
        "metadata_actual_risk_usd": 50.0,
    }
