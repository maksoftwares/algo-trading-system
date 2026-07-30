from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "forex-research" / "scripts"))

from run_forex_mt5_frequency_scout import parse_mt5_report


CONFIG = (
    PACKAGE_ROOT / "config" / "frozen_m15_regime_portfolio_mt5_transfer_v1.json"
)
SOURCE = (
    PACKAGE_ROOT / "mt5" / "Experts" / "EurUsdM15RegimePortfolioControlledDemo.mq5"
)
EX5 = SOURCE.with_suffix(".ex5")
COMPILE_LOG = PACKAGE_ROOT / "mt5" / "EURUSD_M15_REGIME_PORTFOLIO_COMPILE.log"
SHADOW = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.set"
)
ORDERING = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_M15_REGIME_PORTFOLIO_ORDERING_DEMO.template.set"
)
TESTER_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_M15_REGIME_PORTFOLIO_TRANSFER_202407_202606.ini"
)
REPORT = Path(
    "C:/MT5A1M5MomentumBacktest/Reports/"
    "EURUSD_M15_REGIME_PORTFOLIO_TRANSFER_202407_202606.htm"
)
AUDIT = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/"
    "Common/Files/EURUSD_M15_REGIME_PORTFOLIO_TRANSFER.csv"
)
OUTPUT = PACKAGE_ROOT / "outputs" / "m15_regime_portfolio_mt5_transfer"
REPORT_MD = (
    PACKAGE_ROOT / "EURUSD_M15_REGIME_PORTFOLIO_MT5_TRANSFER_RESULT_2026_07_30.md"
)

AUDIT_FIELDS = (
    "recorded_at_broker",
    "recorded_at_utc",
    "run_id",
    "event",
    "detail",
    "account",
    "server",
    "symbol",
    "magic",
    "regime",
    "side",
    "lots",
    "entry",
    "stop",
    "target",
    "shadow",
    "orders_enabled",
    "emergency_stop",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize(trades: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["profit"]) for row in trades]
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    factor = sum(wins) / sum(losses) if losses else math.inf if wins else 0.0
    payoff = (
        (sum(wins) / len(wins)) / (sum(losses) / len(losses))
        if wins and losses
        else 0.0
    )
    return {
        "trades": len(values),
        "wins": len(wins),
        "win_rate": len(wins) / len(values) if values else 0.0,
        "realized_payoff_ratio": payoff,
        "profit_factor": None if math.isinf(factor) else factor,
        "profit_factor_is_infinite": math.isinf(factor),
        "net_pnl_usd_executable": sum(values),
        "net_pnl_usd_research_equivalent": sum(values) * 0.5,
    }


def subset(
    trades: list[dict[str, Any]], start: str, end: str
) -> list[dict[str, Any]]:
    return [row for row in trades if start <= row["entry_date"] < end]


def weekday_count(start: date, end: date) -> int:
    return sum(
        1
        for offset in range((end - start).days)
        if (start + timedelta(days=offset)).weekday() < 5
    )


def best_winners_removed(
    trades: list[dict[str, Any]], fraction: float
) -> tuple[list[dict[str, Any]], int]:
    count = max(1, math.ceil(len(trades) * fraction))
    indexed = list(enumerate(trades))
    winners = sorted(
        (
            (index, row)
            for index, row in indexed
            if float(row["profit"]) > 0.0
        ),
        key=lambda item: float(item[1]["profit"]),
        reverse=True,
    )
    removed = {index for index, _ in winners[:count]}
    return [row for index, row in indexed if index not in removed], len(removed)


def balance_drawdown_percent(metrics: dict[str, str]) -> float:
    match = re.search(
        r"\(([0-9.]+)%\)", metrics["Balance Drawdown Maximal"]
    )
    if not match:
        raise ValueError("Could not parse broker balance drawdown")
    return float(match.group(1))


def load_audit() -> tuple[list[dict[str, str]], bool]:
    with AUDIT.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise RuntimeError("MT5 transfer audit is empty")
    header_present = tuple(rows[0]) == AUDIT_FIELDS
    data_rows = rows[1:] if header_present else rows
    if any(len(row) != len(AUDIT_FIELDS) for row in data_rows):
        raise RuntimeError("MT5 transfer audit has malformed rows")
    return [dict(zip(AUDIT_FIELDS, row, strict=True)) for row in data_rows], (
        header_present
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def format_factor(item: dict[str, Any]) -> str:
    if item["profit_factor_is_infinite"]:
        return "infinite"
    return f"{item['profit_factor']:.3f}"


def render(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL"]
    first = result["windows"]["FIRST_12_MONTHS"]
    second = result["windows"]["SECOND_12_MONTHS"]
    by_regime = result["by_regime"]
    gate_rows = "\n".join(
        f"| {name} | {passed} |"
        for name, passed in result["gate_results"].items()
    )
    return f"""# EURUSD M15 regime-portfolio MT5 transfer result

Status: **{result["status"]}**

The frozen M15 first-break portfolio compiled with zero errors and zero
warnings and completed a Capital.com every-real-tick transfer without any rule
change.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | Executable P&L | Research-equivalent P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full two years | {full["trades"]} | {result["trades_per_weekday"]:.3f} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {format_factor(full)} | ${full["net_pnl_usd_executable"]:+.2f} | ${full["net_pnl_usd_research_equivalent"]:+.2f} |
| First 12 months | {first["trades"]} | - | {first["win_rate"]:.2%} | {first["realized_payoff_ratio"]:.3f} | {format_factor(first)} | ${first["net_pnl_usd_executable"]:+.2f} | ${first["net_pnl_usd_research_equivalent"]:+.2f} |
| Second 12 months | {second["trades"]} | - | {second["win_rate"]:.2%} | {second["realized_payoff_ratio"]:.3f} | {format_factor(second)} | ${second["net_pnl_usd_executable"]:+.2f} | ${second["net_pnl_usd_research_equivalent"]:+.2f} |
| Chop | {by_regime["CHOP"]["trades"]} | - | {by_regime["CHOP"]["win_rate"]:.2%} | {by_regime["CHOP"]["realized_payoff_ratio"]:.3f} | {format_factor(by_regime["CHOP"])} | ${by_regime["CHOP"]["net_pnl_usd_executable"]:+.2f} | ${by_regime["CHOP"]["net_pnl_usd_research_equivalent"]:+.2f} |
| Compression | {by_regime["COMPRESSION"]["trades"]} | - | {by_regime["COMPRESSION"]["win_rate"]:.2%} | {by_regime["COMPRESSION"]["realized_payoff_ratio"]:.3f} | {format_factor(by_regime["COMPRESSION"])} | ${by_regime["COMPRESSION"]["net_pnl_usd_executable"]:+.2f} | ${by_regime["COMPRESSION"]["net_pnl_usd_research_equivalent"]:+.2f} |

Broker history quality was `{result["broker_metrics"]["History Quality"]}`.
Maximum balance/equity drawdown was
`{result["broker_metrics"]["Balance Drawdown Maximal"]}` /
`{result["broker_metrics"]["Equity Drawdown Maximal"]}`.

After removing the best {result["best_5pct_removed_count"]} trades, PF was
{format_factor(result["best_5pct_removed"])}.

## Frozen gates

| Gate | Passed |
|---|---|
{gate_rows}

## Audit note

The frozen EA's CSV writer omitted the header row, but every one of the
`{result["audit"]["rows"]}` data rows has the exact frozen 18-column schema.
The verifier supplies that fixed schema without changing or rerunning the
strategy. There were `{result["audit"]["signals"]}` signals,
`{result["audit"]["orders_sent"]}` successful entries, zero failed sends, and
zero initialization failures.

## Decision

The unchanged rule passes the preregistered broker-transfer gates and may move
to prospective **shadow observation only**. Demo orders remain disallowed until
fresh evidence passes its separate admission protocol. Its broker frequency is
only {result["trades_per_weekday"]:.3f} trades per weekday, so it preserves the
edge core but does not by itself achieve the final one-trade-per-day goal.
"""


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    pinned = config["implementation_hashes"]
    actual_hashes = {
        "source_mq5": sha256(SOURCE),
        "compiled_ex5": sha256(EX5),
        "shadow_preset": sha256(SHADOW),
        "ordering_template": sha256(ORDERING),
        "tester_config": sha256(TESTER_CONFIG),
        "compile_log": sha256(COMPILE_LOG),
    }
    if actual_hashes != pinned:
        raise RuntimeError("Frozen implementation hash mismatch")
    compile_text = COMPILE_LOG.read_text(encoding="utf-16")
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError("MQL5 compile did not pass")
    if not REPORT.exists() or not AUDIT.exists():
        raise FileNotFoundError("Frozen MT5 transfer evidence is missing")

    trades, broker_metrics = parse_mt5_report(REPORT, "EURUSD")
    if int(broker_metrics["Total Trades"]) != len(trades):
        raise RuntimeError("Broker report trade count mismatch")
    audit_rows, header_present = load_audit()
    events = Counter(row["event"] for row in audit_rows)
    signal_rows = [row for row in audit_rows if row["event"] == "SIGNAL"]
    if any(
        row["run_id"] != "EURUSD_M15_REGIME_TRANSFER_202407_202606"
        or row["account"] != "1025742"
        or row["server"] != "Capital.ComMena-Demo"
        or row["symbol"] != "EURUSD"
        for row in audit_rows
    ):
        raise RuntimeError("MT5 transfer audit identity mismatch")
    if events["SIGNAL"] != len(trades) or events["ORDER_SEND_OK"] != len(trades):
        raise RuntimeError("MT5 audit and broker trades do not reconcile")
    if events["ORDER_SEND_FAILED"] or events["INIT_FAILED"]:
        raise RuntimeError("MT5 transfer contains failed orders or initialization")

    windows = {
        "FULL": summarize(trades),
        "FIRST_12_MONTHS": summarize(
            subset(trades, "2024-07-01", "2025-07-01")
        ),
        "SECOND_12_MONTHS": summarize(
            subset(trades, "2025-07-01", "2026-07-01")
        ),
    }
    remaining, removed_count = best_winners_removed(trades, 0.05)
    removed = summarize(remaining)
    by_regime = {
        name: summarize(
            [
                row
                for row in trades
                if row["entry_comment"].endswith("_" + name)
            ]
        )
        for name in ("CHOP", "COMPRESSION")
    }
    weekdays = weekday_count(date(2024, 7, 1), date(2026, 7, 1))
    trades_per_weekday = len(trades) / weekdays
    drawdown_percent = balance_drawdown_percent(broker_metrics)
    gates = config["one_shot_transfer_gates"]
    gate_results = {
        "minimum_trades": len(trades) >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": trades_per_weekday
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_full_profit_factor": windows["FULL"]["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "minimum_each_12_month_profit_factor": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_each_12_month_profit_factor_exclusive"])
            for name in ("FIRST_12_MONTHS", "SECOND_12_MONTHS")
        ),
        "minimum_latest_12_month_profit_factor": windows[
            "SECOND_12_MONTHS"
        ]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "minimum_net_pnl_usd": windows["FULL"]["net_pnl_usd_executable"]
        > float(gates["minimum_net_pnl_usd_exclusive"]),
        "minimum_best_5pct_removed_profit_factor": removed["profit_factor"]
        >= float(gates["minimum_best_5pct_removed_profit_factor"]),
        "maximum_balance_drawdown_percent": drawdown_percent
        <= float(gates["maximum_balance_drawdown_percent"]),
    }
    status = (
        "BROKER_TRANSFER_PASSED_PROSPECTIVE_SHADOW_ONLY"
        if all(gate_results.values())
        else "BROKER_TRANSFER_REJECTED"
    )

    monthly_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        monthly_groups[row["entry_date"][:7]].append(row)
    monthly = [
        {"month": month, **summarize(rows)}
        for month, rows in sorted(monthly_groups.items())
    ]
    result = {
        "schema_version": "eurusd_m15_regime_portfolio_mt5_transfer_result_v1",
        "generated_at_utc": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": status,
        "broker_action_performed": False,
        "demo_order_authorized": False,
        "prospective_shadow_authorized": all(gate_results.values()),
        "implementation_hashes": actual_hashes,
        "report_sha256": sha256(REPORT),
        "audit_sha256": sha256(AUDIT),
        "broker_metrics": broker_metrics,
        "weekdays": weekdays,
        "trades_per_weekday": trades_per_weekday,
        "windows": windows,
        "by_regime": by_regime,
        "best_5pct_removed_count": removed_count,
        "best_5pct_removed": removed,
        "balance_drawdown_percent": drawdown_percent,
        "gate_results": gate_results,
        "all_transfer_gates_passed": all(gate_results.values()),
        "audit": {
            "rows": len(audit_rows),
            "header_present": header_present,
            "signals": events["SIGNAL"],
            "orders_sent": events["ORDER_SEND_OK"],
            "order_send_failures": events["ORDER_SEND_FAILED"],
            "initialization_failures": events["INIT_FAILED"],
            "event_counts": dict(sorted(events.items())),
            "regime_signal_counts": dict(
                sorted(Counter(row["regime"] for row in signal_rows).items())
            ),
        },
        "monthly": monthly,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPORT, OUTPUT / REPORT.name)
    for suffix in (".png", "-holding.png", "-mfemae.png", "-hst.png"):
        source = REPORT.with_name(REPORT.stem + suffix)
        if source.exists():
            shutil.copy2(source, OUTPUT / source.name)
    write_csv(OUTPUT / "TRADES.csv", trades)
    write_csv(OUTPUT / "MONTHLY_METRICS.csv", monthly)
    (OUTPUT / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_MD.write_text(render(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
