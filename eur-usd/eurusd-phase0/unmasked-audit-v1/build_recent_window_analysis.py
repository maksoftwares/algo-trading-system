from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "outputs" / "audit" / "UNMASKED_TRADE_LEDGER_ENRICHED.csv"
OUTPUT_DIR = ROOT / "outputs" / "audit"
OUTPUT_CSV = OUTPUT_DIR / "EURUSD_V1_UNMASKED_RECENT_WINDOWS.csv"
OUTPUT_JSON = OUTPUT_DIR / "EURUSD_V1_UNMASKED_RECENT_WINDOWS.json"
OUTPUT_MD = OUTPUT_DIR / "EURUSD_V1_UNMASKED_RECENT_WINDOWS.md"

TEST_END_EXCLUSIVE = datetime(2026, 7, 2)
STARTING_BALANCE_USD = 1_000.0
WINDOWS = (
    ("3_months", datetime(2026, 4, 2)),
    ("6_months", datetime(2026, 1, 2)),
    ("12_months", datetime(2025, 7, 2)),
)


@dataclass(frozen=True)
class Trade:
    entry_time: datetime
    exit_time: datetime
    price_profit: float
    commission: float
    swap: float
    net: float


def load_trades(path: Path = LEDGER) -> list[Trade]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            Trade(
                entry_time=datetime.strptime(row["entry_time"], "%Y.%m.%d %H:%M:%S"),
                exit_time=datetime.strptime(row["exit_time"], "%Y.%m.%d %H:%M:%S"),
                price_profit=float(row["price_profit"]),
                commission=float(row["commission"]),
                swap=float(row["swap"]),
                net=float(row["net"]),
            )
            for row in csv.DictReader(handle)
        ]


def profit_factor(values: Iterable[float]) -> float | None:
    values = list(values)
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    return gross_profit / gross_loss if gross_loss else None


def closed_trade_drawdown(trades: Iterable[Trade]) -> float:
    equity = 0.0
    peak = 0.0
    maximum_drawdown = 0.0
    for trade in sorted(trades, key=lambda item: item.exit_time):
        equity += trade.net
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, peak - equity)
    return maximum_drawdown


def consecutive_extremes(trades: Iterable[Trade]) -> tuple[int, int]:
    maximum_wins = maximum_losses = current_wins = current_losses = 0
    for trade in sorted(trades, key=lambda item: item.exit_time):
        if trade.net > 0:
            current_wins += 1
            current_losses = 0
            maximum_wins = max(maximum_wins, current_wins)
        elif trade.net < 0:
            current_losses += 1
            current_wins = 0
            maximum_losses = max(maximum_losses, current_losses)
    return maximum_wins, maximum_losses


def stressed_value(trade: Trade, round_trip_pips: float) -> float:
    # At 0.01 lot on standard EURUSD, one pip is USD 0.10.
    execution_drag = round_trip_pips * 0.10
    stressed_commission = trade.commission * (1.25 if trade.commission < 0 else 1.0)
    stressed_swap = trade.swap * (1.25 if trade.swap < 0 else 1.0)
    return trade.price_profit - execution_drag + stressed_commission + stressed_swap


def measure_window(name: str, start: datetime, trades: Iterable[Trade]) -> dict[str, object]:
    selected = sorted(
        (
            trade
            for trade in trades
            if start <= trade.exit_time < TEST_END_EXCLUSIVE
        ),
        key=lambda item: item.exit_time,
    )
    wins = [trade.net for trade in selected if trade.net > 0]
    losses = [trade.net for trade in selected if trade.net < 0]
    net_values = [trade.net for trade in selected]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    net = sum(net_values)
    average_win = gross_profit / len(wins)
    average_loss = gross_loss / len(losses)
    payoff_ratio = average_win / average_loss
    primary = [stressed_value(trade, 0.5) for trade in selected]
    severe = [stressed_value(trade, 1.0) for trade in selected]
    maximum_wins, maximum_losses = consecutive_extremes(selected)
    average_duration_minutes = sum(
        (trade.exit_time - trade.entry_time).total_seconds() / 60 for trade in selected
    ) / len(selected)

    return {
        "window": name,
        "from_inclusive": start.strftime("%Y-%m-%d"),
        "to_exclusive": TEST_END_EXCLUSIVE.strftime("%Y-%m-%d"),
        "trade_assignment": "realized exit timestamp",
        "trades": len(selected),
        "wins": len(wins),
        "losses": len(losses),
        "flat": len(selected) - len(wins) - len(losses),
        "win_rate_pct": round(100 * len(wins) / len(selected), 4),
        "net_usd": round(net, 2),
        "return_on_1000_pct": round(100 * net / STARTING_BALANCE_USD, 4),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4),
        "average_trade_usd": round(net / len(selected), 4),
        "average_win_usd": round(average_win, 4),
        "average_loss_usd": round(-average_loss, 4),
        "payoff_ratio": round(payoff_ratio, 4),
        "breakeven_win_rate_pct": round(100 / (1 + payoff_ratio), 4),
        "closed_trade_max_drawdown_usd": round(closed_trade_drawdown(selected), 2),
        "largest_win_usd": round(max(net_values), 2),
        "largest_loss_usd": round(min(net_values), 2),
        "maximum_consecutive_wins": maximum_wins,
        "maximum_consecutive_losses": maximum_losses,
        "average_holding_minutes": round(average_duration_minutes, 1),
        "primary_stress_net_usd": round(sum(primary), 2),
        "primary_stress_profit_factor": round(profit_factor(primary) or 0.0, 4),
        "severe_stress_net_usd": round(sum(severe), 2),
        "severe_stress_profit_factor": round(profit_factor(severe) or 0.0, 4),
    }


def render_markdown(results: list[dict[str, object]]) -> str:
    labels = {"3_months": "3 months", "6_months": "6 months", "12_months": "1 year"}
    lines = [
        "# EURUSD V1 Unmasked Recent-Window Analysis",
        "",
        "This is retrospective MT5 Strategy Tester evidence, not live-account profit.",
        "The test endpoint is `2026-07-02` exclusive; the final realized trade exits",
        "on `2026-07-01`. Trades are assigned to windows by exit timestamp.",
        "",
        "The account starts at USD 1,000 and every position uses 0.01 lot.",
        "",
        "| Period | Trades | W / L | Win rate | Net USD | Return | PF | Avg/trade | Closed-trade DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| {label} | {trades} | {wins} / {losses} | {win_rate_pct:.2f}% | "
            "{net_usd:+.2f} | {return_on_1000_pct:+.2f}% | {profit_factor:.3f} | "
            "{average_trade_usd:+.4f} | {closed_trade_max_drawdown_usd:.2f} |".format(
                label=labels[str(result["window"])], **result
            )
        )

    lines.extend(
        [
            "",
            "## Payoff geometry",
            "",
            "| Period | Avg win | Avg loss | Payoff ratio | Break-even WR | Actual WR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for result in results:
        lines.append(
            "| {label} | {average_win_usd:.4f} | {average_loss_usd:.4f} | "
            "{payoff_ratio:.4f} | {breakeven_win_rate_pct:.2f}% | "
            "{win_rate_pct:.2f}% |".format(
                label=labels[str(result["window"])], **result
            )
        )

    lines.extend(
        [
            "",
            "## Cost stress",
            "",
            "Primary stress adds 0.5 pip round-trip adverse execution and multiplies",
            "negative commission/swap by 1.25. Severe stress adds 1.0 pip with the",
            "same negative-cost multiplier.",
            "",
            "| Period | Primary net | Primary PF | Severe net | Severe PF |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for result in results:
        lines.append(
            "| {label} | {primary_stress_net_usd:+.2f} | "
            "{primary_stress_profit_factor:.3f} | {severe_stress_net_usd:+.2f} | "
            "{severe_stress_profit_factor:.3f} |".format(
                label=labels[str(result["window"])], **result
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The one-year base PF is only 1.0167 and its average trade is USD 0.0096.",
            "Primary cost stress makes the one-year result negative. Recent positive",
            "three- and six-month totals therefore do not establish a robust edge.",
            "",
            "`closed_trade_max_drawdown_usd` is reconstructed from realized trade",
            "outcomes with each window rebased to zero. It is not MT5 intratrade or",
            "floating-equity drawdown.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(results: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "schema_version": "eurusd_v1_unmasked_recent_windows_v1",
                "candidate_id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT",
                "status": "RETROSPECTIVE_RESEARCH_ONLY",
                "test_end_exclusive": TEST_END_EXCLUSIVE.strftime("%Y-%m-%d"),
                "starting_balance_usd": STARTING_BALANCE_USD,
                "lot_size": 0.01,
                "windows": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    OUTPUT_MD.write_text(render_markdown(results), encoding="utf-8", newline="\n")


def main() -> int:
    trades = load_trades()
    results = [measure_window(name, start, trades) for name, start in WINDOWS]
    write_outputs(results)
    print(f"Wrote {len(results)} recent-window rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
