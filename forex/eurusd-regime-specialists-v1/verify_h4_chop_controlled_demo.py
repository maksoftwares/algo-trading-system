from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "forex-research" / "scripts"))

from run_forex_mt5_frequency_scout import parse_mt5_report

OLD_REPORT = (
    REPO_ROOT
    / "eur-usd"
    / "eurusd-fast-research"
    / "regime-specialists-v2"
    / "outputs"
    / "capital_mt5_real_tick"
    / "EURUSD_CAPV2_CHOP_ORDERING_TESTER_202407_202606.htm"
)
OLD_VERDICT = OLD_REPORT.with_name("VERDICT.json")
TESTER_ROOT = Path("C:/MT5A1M5MomentumBacktest")
NEW_REPORT = (
    TESTER_ROOT
    / "Reports"
    / "EURUSD_H4_CHOP_CONTROLLED_PARITY_202407_202606.htm"
)
SOURCE = PACKAGE_ROOT / "mt5" / "Experts" / "EurUsdH4ChopControlledDemo.mq5"
EX5 = PACKAGE_ROOT / "mt5" / "Experts" / "EurUsdH4ChopControlledDemo.ex5"
COMPILE_LOG = (
    PACKAGE_ROOT / "mt5" / "EURUSD_H4_CHOP_CONTROLLED_DEMO_COMPILE.log"
)
PARITY_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_CHOP_CONTROLLED_PARITY_202407_202606.ini"
)
SHADOW_PRESET = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_CHOP_CONTROLLED_SHADOW_DEMO.set"
)
ORDERING_TEMPLATE = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_CHOP_CONTROLLED_ORDERING_DEMO.template.set"
)
OUTPUT = PACKAGE_ROOT / "outputs" / "h4_chop_controlled_demo"
REPORT_MD = (
    PACKAGE_ROOT / "EURUSD_H4_CHOP_CONTROLLED_DEMO_VERIFICATION_2026_07_30.md"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def profit_factor(values: list[float]) -> float:
    gains = sum(value for value in values if value > 0.0)
    losses = -sum(value for value in values if value < 0.0)
    return gains / losses if losses else (math.inf if gains else 0.0)


def summarize(trades: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["profit"]) for row in trades]
    wins = [value for value in values if value > 0.0]
    losses = [value for value in values if value < 0.0]
    payoff = (
        sum(wins) / len(wins) / (-sum(losses) / len(losses))
        if wins and losses
        else 0.0
    )
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    factor = profit_factor(values)
    return {
        "trades": len(values),
        "wins": len(wins),
        "win_rate": len(wins) / len(values) if values else 0.0,
        "realized_payoff_ratio_usd": payoff,
        "profit_factor": None if math.isinf(factor) else factor,
        "profit_factor_is_infinite": math.isinf(factor),
        "net_pnl_usd_001_lot": sum(values),
        "maximum_closed_trade_drawdown_usd": drawdown,
    }


def subset(
    trades: list[dict[str, Any]], start: str, end: str
) -> list[dict[str, Any]]:
    return [
        row
        for row in trades
        if start <= row["entry_time"].replace(".", "-")[:10] < end
    ]


def calendar_months(start: str, end: str) -> list[str]:
    year, month = map(int, start[:7].split("-"))
    end_key = end[:7]
    result = []
    while f"{year:04d}-{month:02d}" < end_key:
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return result


def monthly(
    trades: list[dict[str, Any]],
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        grouped[row["entry_time"][:7].replace(".", "-")].append(row)
    months = calendar_months(start, end) if start and end else sorted(grouped)
    return [{"month": month, **summarize(grouped[month])} for month in months]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def render(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL"]
    latest12 = result["windows"]["LATEST_12_MONTHS"]
    latest6 = result["windows"]["LATEST_6_MONTHS"]
    def formatted_factor(item: dict[str, Any]) -> str:
        return (
            "infinite"
            if item["profit_factor_is_infinite"]
            else f"{item['profit_factor']:.3f}"
        )

    rows = "\n".join(
        f"| {item['month']} | {item['trades']} | {item['win_rate']:.1%} | "
        f"{item['realized_payoff_ratio_usd']:.3f} | "
        f"{formatted_factor(item)} | "
        f"${item['net_pnl_usd_001_lot']:+.2f} |"
        for item in result["latest_12_months_by_month"]
    )
    return f"""# EURUSD H4 chop controlled demo verification

Status: **{result["status"]}**

The hardened EA compiled with zero errors and zero warnings. Its broker
Strategy Tester run exactly reproduced all 62 prior trade rows and aggregate
metrics from July 2024 through June 2026.

| Window | Trades | Win rate | Payoff | PF | Fixed 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|
| Full broker window | {full["trades"]} | {full["win_rate"]:.1%} | {full["realized_payoff_ratio_usd"]:.3f} | {formatted_factor(full)} | ${full["net_pnl_usd_001_lot"]:+.2f} |
| Latest 12 months | {latest12["trades"]} | {latest12["win_rate"]:.1%} | {latest12["realized_payoff_ratio_usd"]:.3f} | {formatted_factor(latest12)} | ${latest12["net_pnl_usd_001_lot"]:+.2f} |
| Latest 6 months | {latest6["trades"]} | {latest6["win_rate"]:.1%} | {latest6["realized_payoff_ratio_usd"]:.3f} | {formatted_factor(latest6)} | ${latest6["net_pnl_usd_001_lot"]:+.2f} |

Broker-reported maximum balance drawdown was $11.00 (0.11%) and maximum
equity drawdown was $14.82 (0.15%) on a $10,000 test deposit.

## Latest 12 calendar months

| Month | Trades | Win rate | Payoff | PF | Fixed 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|
{rows}

## Decision

The compiled artifact and disarmed shadow preset are ready for controlled demo
observation. The ordering preset intentionally remains a template: the owner
must enter the exact demo account and server allowlist. No live account is
supported. Sparse frequency and inspected-history bias prevent any claim of a
production-ready trading edge.
"""


def main() -> None:
    required = (
        OLD_REPORT,
        OLD_VERDICT,
        NEW_REPORT,
        SOURCE,
        EX5,
        COMPILE_LOG,
        PARITY_CONFIG,
        SHADOW_PRESET,
        ORDERING_TEMPLATE,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)
    compile_text = COMPILE_LOG.read_text(encoding="utf-16", errors="ignore")
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError("MQL5 compile did not pass the zero-warning gate")
    old_trades, old_metrics = parse_mt5_report(OLD_REPORT, "EURUSD")
    new_trades, new_metrics = parse_mt5_report(NEW_REPORT, "EURUSD")
    parity_fields = (
        "entry_time",
        "direction",
        "volume",
        "entry_price",
        "exit_time",
        "exit_price",
        "profit",
        "balance",
    )
    rows_match = len(old_trades) == len(new_trades) and all(
        all(old[field] == new[field] for field in parity_fields)
        for old, new in zip(old_trades, new_trades, strict=True)
    )
    metrics_match = old_metrics == new_metrics
    if not rows_match or not metrics_match:
        raise RuntimeError("Hardened EA failed exact broker trade parity")

    result = {
        "schema_version": "eurusd_h4_chop_controlled_demo_verification_v1",
        "generated_at_utc": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": "CONTROLLED_SHADOW_DEMO_ARTIFACT_READY",
        "production_ready": False,
        "live_ready": False,
        "ordering_demo_armed": False,
        "owner_identity_required_for_ordering_demo": True,
        "broker_action_performed": False,
        "exact_prior_trade_row_parity": rows_match,
        "exact_prior_metric_parity": metrics_match,
        "history_quality": new_metrics["History Quality"],
        "broker_reported": new_metrics,
        "windows": {
            "FULL": summarize(new_trades),
            "LATEST_12_MONTHS": summarize(
                subset(new_trades, "2025-07-01", "2026-07-01")
            ),
            "LATEST_6_MONTHS": summarize(
                subset(new_trades, "2026-01-01", "2026-07-01")
            ),
        },
        "latest_12_months_by_month": monthly(
            subset(new_trades, "2025-07-01", "2026-07-01"),
            start="2025-07-01",
            end="2026-07-01",
        ),
        "hashes": {
            "source_mq5": sha256(SOURCE),
            "compiled_ex5": sha256(EX5),
            "compile_log": sha256(COMPILE_LOG),
            "parity_config": sha256(PARITY_CONFIG),
            "shadow_preset": sha256(SHADOW_PRESET),
            "ordering_template": sha256(ORDERING_TEMPLATE),
            "new_broker_report": sha256(NEW_REPORT),
            "prior_broker_report": sha256(OLD_REPORT),
        },
        "safety": {
            "demo_account_type_required": True,
            "exact_account_allowlist_required_for_orders": True,
            "exact_server_allowlist_required_for_orders": True,
            "live_account_hard_rejection": True,
            "default_shadow_mode": True,
            "default_orders_disabled": True,
            "default_emergency_stop": True,
            "fixed_lots": 0.01,
            "maximum_positions_on_eurusd": 1,
            "maximum_entries_per_utc_day": 1,
            "maximum_spread_pips": 2.0,
            "daily_closed_loss_breaker_usd": 10.0,
            "rolling_5day_closed_loss_breaker_usd": 20.0,
            "session_equity_drawdown_breaker_usd": 25.0,
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NEW_REPORT, OUTPUT / NEW_REPORT.name)
    for suffix in (".png", "-holding.png", "-mfemae.png", "-hst.png"):
        source = NEW_REPORT.with_name(NEW_REPORT.stem + suffix)
        if source.exists():
            shutil.copy2(source, OUTPUT / source.name)
    write_csv(OUTPUT / "TRADES.csv", new_trades)
    write_csv(OUTPUT / "LATEST_12_MONTHS.csv", result["latest_12_months_by_month"])
    (OUTPUT / "VERIFICATION.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_MD.write_text(render(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
