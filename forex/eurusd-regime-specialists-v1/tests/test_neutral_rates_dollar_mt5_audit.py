from __future__ import annotations

from pathlib import Path

from eurusd_regime_specialists.neutral_rates_dollar_mt5_audit import (
    evaluate_gates,
    read_mt5_report,
    reconcile_report,
)


def test_parser_includes_swap_in_trade_net(tmp_path: Path) -> None:
    report = tmp_path / "report.htm"
    report.write_text(
        """
        <table>
        <tr><td>Total Net Profit:</td><td>1.25</td></tr>
        <tr><td>Gross Profit:</td><td>1.25</td></tr>
        <tr><td>Gross Loss:</td><td>0.00</td></tr>
        <tr><td>Profit Factor:</td><td></td></tr>
        <tr><td>Total Trades:</td><td>1</td></tr>
        <tr>
          <td>2026.01.02 00:00:00</td><td>1</td><td>EURUSD</td>
          <td>sell</td><td>in</td><td>0.01</td><td>1.10000</td>
          <td>1</td><td>0.00</td><td>0.00</td><td>0.00</td>
          <td>1000.00</td><td>entry</td>
        </tr>
        <tr>
          <td>2026.01.02 04:00:00</td><td>2</td><td>EURUSD</td>
          <td>buy</td><td>out</td><td>0.01</td><td>1.09900</td>
          <td>2</td><td>0.00</td><td>0.25</td><td>1.00</td>
          <td>1001.25</td><td>tp</td>
        </tr>
        </table>
        """,
        encoding="utf-16",
    )
    trades, reported = read_mt5_report(report)
    assert len(trades) == 1
    assert trades.iloc[0]["net_pnl_usd"] == 1.25
    assert reported["Total Net Profit"] == "1.25"


def test_reconciliation_uses_net_trade_accounting(
    tmp_path: Path,
) -> None:
    report = tmp_path / "report.htm"
    report.write_text(
        """
        <table>
        <tr><td>Total Net Profit:</td><td>-0.50</td></tr>
        <tr><td>Gross Profit:</td><td>0.00</td></tr>
        <tr><td>Gross Loss:</td><td>-0.50</td></tr>
        <tr><td>Profit Factor:</td><td>0.00</td></tr>
        <tr><td>Total Trades:</td><td>1</td></tr>
        <tr>
          <td>2026.01.02 00:00:00</td><td>1</td><td>EURUSD</td>
          <td>sell</td><td>in</td><td>0.01</td><td>1.10000</td>
          <td>1</td><td>0.00</td><td>0.00</td><td>0.00</td>
          <td>1000.00</td><td>entry</td>
        </tr>
        <tr>
          <td>2026.01.02 04:00:00</td><td>2</td><td>EURUSD</td>
          <td>buy</td><td>out</td><td>0.01</td><td>1.10050</td>
          <td>2</td><td>0.00</td><td>0.00</td><td>-0.50</td>
          <td>999.50</td><td>sl</td>
        </tr>
        </table>
        """,
        encoding="utf-16",
    )
    trades, reported = read_mt5_report(report)
    result = reconcile_report(trades, reported)
    assert all(result["exact_accounting_checks"].values())


def test_weak_small_neutral_slice_is_rejected() -> None:
    metrics = {
        "trades": 12,
        "win_rate": 2 / 3,
        "realized_payoff_ratio": 0.73,
        "profit_factor": 1.46,
        "top_5pct_removed_profit_factor": 1.13,
    }
    chronology = {
        "LATEST_SIX_MONTHS": {"trades": 1},
        "RECENT_2024_2026_H1": {"net_pnl_usd": -9.16},
        "2025": {"net_pnl_usd": -17.75},
    }
    robustness = {
        "PRIMARY_OFFSET_0": metrics,
        "ROBUSTNESS_OFFSET_2": {**metrics, "profit_factor": 1.14},
        "ROBUSTNESS_OFFSET_3": {**metrics, "profit_factor": 1.14},
    }
    gates = evaluate_gates(metrics, chronology, robustness)
    assert gates["primary_profit_factor_at_least_1p15"]
    assert not gates["all_offset_profit_factors_at_least_1p15"]
    assert not gates["minimum_30_neutral_trades"]
    assert not all(gates.values())
