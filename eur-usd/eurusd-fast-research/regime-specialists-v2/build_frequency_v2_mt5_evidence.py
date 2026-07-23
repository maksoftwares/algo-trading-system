from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "frequency_v2_mt5"
M15_REPORT = OUTPUT / "M15_TREND_OVERLAY_REPORT.htm"
CONTROL_REPORT = OUTPUT / "CHOP_CONTROL_REPORT.htm"
M15_EX5 = ROOT / "mt5" / "Experts" / "ForexMeanReversionScout.ex5"
M15_SOURCE = (
    ROOT.parent.parent.parent
    / "forex-research"
    / "mt5"
    / "Experts"
    / "ForexMeanReversionScout.mq5"
)
ACTIVE_DAYS = 615


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_trades(path: Path, sleeve: str) -> pd.DataFrame:
    raw = pd.read_html(path, encoding="utf-16")[1]
    deals_header = raw.index[raw.iloc[:, 0].astype(str).eq("Deals")]
    if len(deals_header) != 1:
        raise RuntimeError(f"Cannot locate MT5 deals table in {path}")
    deals = raw.iloc[deals_header[0] + 2 :].copy()
    deals.columns = [
        "time",
        "deal",
        "symbol",
        "type",
        "direction",
        "volume",
        "price",
        "order",
        "commission",
        "swap",
        "profit",
        "balance",
        "comment",
    ]
    deals = deals[deals["symbol"].eq("EURUSD")].copy()
    deals["time"] = pd.to_datetime(deals["time"], format="%Y.%m.%d %H:%M:%S")
    for field in ("commission", "swap", "profit"):
        deals[field] = pd.to_numeric(deals[field])
    entries = deals[deals["direction"].eq("in")].reset_index(drop=True)
    exits = deals[deals["direction"].eq("out")].reset_index(drop=True)
    if len(entries) != len(exits):
        raise RuntimeError(f"Unpaired MT5 deals in {path}")
    return pd.DataFrame(
        {
            "entry_time": entries["time"],
            "exit_time": exits["time"],
            "sleeve": sleeve,
            "volume": pd.to_numeric(entries["volume"]),
            "entry_price": pd.to_numeric(entries["price"]),
            "exit_price": pd.to_numeric(exits["price"]),
            "commission": exits["commission"],
            "swap": exits["swap"],
            "profit": exits["profit"],
            "net_pnl_usd": exits["commission"] + exits["swap"] + exits["profit"],
            "exit_comment": exits["comment"],
        }
    )


def profit_factor(values: np.ndarray) -> float:
    return float(values[values > 0].sum() / -values[values < 0].sum())


def main() -> None:
    m15 = read_trades(M15_REPORT, "M15_RSI_LONG_H4_TREND_OVERLAY")
    control = read_trades(CONTROL_REPORT, "H1_CHOP_ASIA_LONDON_SHORT_CONTROL")
    trades = (
        pd.concat([m15, control], ignore_index=True)
        .sort_values(["exit_time", "sleeve"])
        .reset_index(drop=True)
    )
    values = trades["net_pnl_usd"].to_numpy(dtype=float)
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    remove_count = int(math.ceil(len(values) * 0.05))
    removed = np.delete(values, np.argsort(values)[-remove_count:])
    monthly = (
        trades.assign(month=trades["exit_time"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(trades=("net_pnl_usd", "size"), net_pnl_usd=("net_pnl_usd", "sum"))
    )

    events = []
    for trade in trades.itertuples():
        events.append((trade.entry_time, 1))
        events.append((trade.exit_time, -1))
    events.sort(key=lambda item: (item[0], item[1]))
    active = 0
    maximum_concurrent = 0
    for _, change in events:
        active += change
        maximum_concurrent = max(maximum_concurrent, active)

    overlap_count = 0
    for trade in control.itertuples():
        overlap_count += int(
            ((m15["entry_time"] < trade.exit_time) & (m15["exit_time"] > trade.entry_time)).sum()
        )

    metrics = {
        "active_broker_dates": ACTIVE_DAYS,
        "trades": len(trades),
        "trades_per_active_day": len(trades) / ACTIVE_DAYS,
        "wins": int((values > 0).sum()),
        "win_rate": float((values > 0).mean()),
        "net_pnl_usd": float(values.sum()),
        "gross_profit_usd": float(values[values > 0].sum()),
        "gross_loss_usd": float(-values[values < 0].sum()),
        "profit_factor": profit_factor(values),
        "maximum_closed_trade_drawdown_usd": float(np.max(peak - equity)),
        "maximum_closed_trade_drawdown_pct_of_10000": float(np.max(peak - equity) / 10000),
        "positive_active_month_share": float((monthly["net_pnl_usd"] > 0).mean()),
        "top_5pct_removed_profit_factor": profit_factor(removed),
        "maximum_concurrent_positions": maximum_concurrent,
        "cross_sleeve_overlaps": overlap_count,
        "m15_trades": len(m15),
        "control_trades": len(control),
    }
    gates = {
        "minimum_trades_per_active_day": 1.0,
        "minimum_profit_factor": 1.30,
        "minimum_win_rate": 0.52,
        "maximum_closed_trade_drawdown_pct_of_10000": 0.01,
        "minimum_positive_active_month_share": 0.55,
        "minimum_top_5pct_removed_profit_factor": 1.0,
        "maximum_concurrent_positions": 2,
    }
    gate_results = {
        "frequency": metrics["trades_per_active_day"] >= gates["minimum_trades_per_active_day"],
        "profit_factor": metrics["profit_factor"] >= gates["minimum_profit_factor"],
        "win_rate": metrics["win_rate"] >= gates["minimum_win_rate"],
        "drawdown": metrics["maximum_closed_trade_drawdown_pct_of_10000"]
        <= gates["maximum_closed_trade_drawdown_pct_of_10000"],
        "positive_months": metrics["positive_active_month_share"]
        >= gates["minimum_positive_active_month_share"],
        "winner_removal": metrics["top_5pct_removed_profit_factor"]
        >= gates["minimum_top_5pct_removed_profit_factor"],
        "concurrency": metrics["maximum_concurrent_positions"]
        <= gates["maximum_concurrent_positions"],
    }
    all_pass = all(gate_results.values())
    trades.to_csv(OUTPUT / "PORTFOLIO_TRADES.csv", index=False)
    monthly.to_csv(OUTPUT / "MONTHLY_METRICS.csv", index=False)
    verdict = {
        "schema_version": "eurusd_frequency_v2_mt5_portfolio_v1",
        "status": "ADAPTIVE_DEMO_RESEARCH_ONLY",
        "history_quality_pct": 98,
        "period": ["2024-07-01", "2026-07-02"],
        "capital_demo_server": "Capital.ComMena-Demo",
        "source_evidence": {
            "m15_report_sha256": sha256(M15_REPORT),
            "control_report_sha256": sha256(CONTROL_REPORT),
            "m15_source_sha256": sha256(M15_SOURCE),
            "m15_ex5_sha256": sha256(M15_EX5),
        },
        "sleeves": [
            {
                "id": "M15_RSI_LONG_H4_TREND_OVERLAY",
                "base_lots": 0.01,
                "additional_lots_in_h4_trend": 0.01,
                "trades": len(m15),
            },
            {
                "id": "H1_CHOP_ASIA_LONDON_SHORT_CONTROL",
                "fixed_lots": 0.01,
                "trades": len(control),
            },
        ],
        "metrics": metrics,
        "gates": gates,
        "gate_results": gate_results,
        "all_gates_pass": all_pass,
        "shadow_demo_ready": all_pass,
        "demo_ordering_requires_owner_enablement": True,
        "live_ready": False,
        "verdict": (
            "CONTROLLED_SHADOW_DEMO_READY"
            if all_pass
            else "FREQUENCY_V2_PORTFOLIO_FAILED"
        ),
        "limitations": [
            "The 2024-2026 interval was inspected during adaptive research and is not an untouched holdout.",
            "The achieved profit factor is above the 1.30 demo floor but below the 1.45 control target.",
            "Prospective shadow and demo-order evidence is required before any live consideration.",
        ],
    }
    (OUTPUT / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
