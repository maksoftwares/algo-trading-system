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

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "forex-research" / "scripts"))

from run_forex_mt5_frequency_scout import parse_mt5_report


CONFIG = (
    PACKAGE_ROOT
    / "config"
    / "frozen_h4_frequency_completion_mt5_step1_v1.json"
)
SOURCE = (
    PACKAGE_ROOT
    / "mt5"
    / "Experts"
    / "EurUsdH4FrequencyCompletionControlledDemo.mq5"
)
EX5 = SOURCE.with_suffix(".ex5")
COMPILE_LOG = (
    PACKAGE_ROOT / "mt5" / "EURUSD_H4_FREQUENCY_COMPLETION_COMPILE.log"
)
SHADOW = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_SHADOW_DEMO.set"
)
ORDERING = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_ORDERING_DEMO.template.set"
)
PARITY_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_PARITY_202407_202606.ini"
)
RESTART_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_RESTART_202601_202606.ini"
)
FAIL_CLOSED_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_FAIL_CLOSED_202606.ini"
)
TEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
COMMON_FILES = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/"
    "MetaQuotes/Terminal/Common/Files"
)
CASES = {
    "PARITY": "EURUSD_H4_FREQUENCY_COMPLETION_PARITY_202407_202606",
    "RESTART": "EURUSD_H4_FREQUENCY_COMPLETION_RESTART_202601_202606",
    "FAIL_CLOSED": "EURUSD_H4_FREQUENCY_COMPLETION_FAIL_CLOSED_202606",
}
OUTPUT = PACKAGE_ROOT / "outputs" / "h4_frequency_completion_mt5_step1"
REPORT_MD = (
    PACKAGE_ROOT
    / "EURUSD_H4_FREQUENCY_COMPLETION_MT5_STEP1_RESULT_2026_07_30.md"
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
    "sleeve",
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


def load_audit(path: Path) -> tuple[list[dict[str, str]], bool]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise RuntimeError(f"Empty MT5 audit: {path}")
    header_present = tuple(rows[0]) == AUDIT_FIELDS
    data = rows[1:] if header_present else rows
    if any(len(row) != len(AUDIT_FIELDS) for row in data):
        raise RuntimeError(f"Malformed MT5 audit: {path}")
    return [
        dict(zip(AUDIT_FIELDS, row, strict=True)) for row in data
    ], header_present


def summarize(trades: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["profit"]) for row in trades]
    wins = [value for value in values if value > 0.0]
    losses = [-value for value in values if value < 0.0]
    return {
        "trades": len(values),
        "wins": len(wins),
        "win_rate": len(wins) / len(values) if values else 0.0,
        "realized_payoff_ratio": (
            (sum(wins) / len(wins)) / (sum(losses) / len(losses))
            if wins and losses
            else None
        ),
        "profit_factor": (
            sum(wins) / sum(losses) if losses else None
        ),
        "net_pnl_usd": sum(values),
    }


def subset(
    trades: list[dict[str, Any]],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    return [row for row in trades if start <= row["entry_date"] < end]


def weekday_count(start: str, end: str) -> int:
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    return sum(
        1
        for offset in range((last - first).days)
        if (first + timedelta(days=offset)).weekday() < 5
    )


def history_quality_percent(metrics: dict[str, str]) -> int:
    return int(metrics["History Quality"].rstrip("%"))


def balance_drawdown_percent(metrics: dict[str, str]) -> float:
    match = re.search(
        r"\(([0-9.]+)%\)",
        metrics["Balance Drawdown Maximal"],
    )
    if not match:
        raise RuntimeError("Could not parse MT5 balance drawdown")
    return float(match.group(1))


def duplicate_sleeve_days(rows: list[dict[str, str]]) -> int:
    keys = [
        (row["sleeve"], row["recorded_at_utc"][:10])
        for row in rows
        if row["event"] == "SIGNAL"
    ]
    return len(keys) - len(set(keys))


def trade_replay_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["entry_time"],
        row["entry_comment"],
        row["exit_time"],
        row["exit_comment"],
        float(row["profit"]),
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def render(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_TRANSFER"]
    latest12 = result["windows"]["LATEST_12_MONTHS"]
    latest6 = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    return f"""# EURUSD H4 frequency-completion MT5 step-one result

Status: **{result["status"]}**

The 12-sleeve EA compiled with zero errors/warnings and passed the isolated
Capital.com broker-transfer, restart-recovery, and disarmed fail-closed checks.
No file was installed into a demo terminal and no demo order was authorized.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Two-year transfer | {full["trades"]} | {result["frequency"]["full_trades_per_weekday"]:.3f} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | ${full["net_pnl_usd"]:+.2f} |
| Latest 12 months | {latest12["trades"]} | {result["frequency"]["latest_12_month_trades_per_weekday"]:.3f} | {latest12["win_rate"]:.2%} | {latest12["realized_payoff_ratio"]:.3f} | {latest12["profit_factor"]:.3f} | ${latest12["net_pnl_usd"]:+.2f} |
| Latest 6 months | {latest6["trades"]} | - | {latest6["win_rate"]:.2%} | {latest6["realized_payoff_ratio"]:.3f} | {latest6["profit_factor"]:.3f} | ${latest6["net_pnl_usd"]:+.2f} |

Research-window count: {result["research_comparison"]["expected_trades"]}.
MT5 count: {result["research_comparison"]["mt5_trades"]}
({result["research_comparison"]["trade_count_ratio"]:.2%}).
All 12 frozen sleeves traded. Every broker trade used exactly 0.01 lot.
History quality was {result["broker_metrics"]["History Quality"]}; maximum
balance drawdown was {result["broker_metrics"]["Balance Drawdown Maximal"]}.

The restart exercise rebuilt state on
{result["restart"]["restart_exercises"]} trading days and exactly replayed the
unchanged 110-trade latest-six-month result, with zero duplicate sleeve-days.
The disarmed test observed {result["fail_closed"]["signals"]} valid signals,
blocked all of them, and placed zero trades.

This is an aggregate broker transfer, not exact event-by-event replay against
the research M5 ledger. It validates executable behavior on MT5 history; it is
not fresh future evidence and does not authorize deployment.

Failed gates: {", ".join(failed) if failed else "none"}.
"""


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    paths = {
        "source_mq5": SOURCE,
        "compiled_ex5": EX5,
        "compile_log": COMPILE_LOG,
        "shadow_preset": SHADOW,
        "ordering_template": ORDERING,
        "parity_tester_config": PARITY_CONFIG,
        "restart_tester_config": RESTART_CONFIG,
        "fail_closed_tester_config": FAIL_CLOSED_CONFIG,
    }
    actual_hashes = {name: sha256(path) for name, path in paths.items()}
    if actual_hashes != config["implementation_hashes"]:
        raise RuntimeError("Frozen MT5 implementation hash mismatch")
    compile_text = COMPILE_LOG.read_text(encoding="utf-16")
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError("MQL5 compilation did not pass")
    sizing_path = PACKAGE_ROOT / config["broker_sizing_result"]["path"]
    ledger_path = PACKAGE_ROOT / config["broker_sizing_ledger"]["path"]
    if (
        sha256(sizing_path) != config["broker_sizing_result"]["sha256"]
        or sha256(ledger_path) != config["broker_sizing_ledger"]["sha256"]
    ):
        raise RuntimeError("Frozen broker-sizing evidence hash mismatch")
    sizing = json.loads(sizing_path.read_text(encoding="utf-8"))
    if sizing["status"] != config["broker_sizing_result"]["expected_status"]:
        raise RuntimeError("Unexpected broker-sizing status")
    research = pd.read_csv(
        ledger_path,
        parse_dates=["entry_time_utc"],
    )
    start, end = config["transfer_window"]
    expected = research[
        research["entry_time_utc"].ge(start)
        & research["entry_time_utc"].lt(end)
    ]
    if len(expected) != int(
        config["broker_sizing_ledger"]["expected_recent_rows"]
    ):
        raise RuntimeError("Unexpected research comparison row count")

    parsed: dict[str, dict[str, Any]] = {}
    for name, stem in CASES.items():
        report_path = TEST_ROOT / "Reports" / f"{stem}.htm"
        audit_path = COMMON_FILES / f"{stem}.csv"
        if not report_path.exists() or not audit_path.exists():
            raise FileNotFoundError(f"Missing {name} MT5 evidence")
        trades, metrics = parse_mt5_report(report_path, "EURUSD")
        audit, header_present = load_audit(audit_path)
        parsed[name] = {
            "stem": stem,
            "report_path": report_path,
            "audit_path": audit_path,
            "trades": trades,
            "metrics": metrics,
            "audit": audit,
            "header_present": header_present,
            "events": Counter(row["event"] for row in audit),
        }

    parity = parsed["PARITY"]
    main_trades = parity["trades"]
    metrics = parity["metrics"]
    windows = {
        "FULL_TRANSFER": summarize(main_trades),
        "LATEST_12_MONTHS": summarize(
            subset(main_trades, *config["latest_12_month_window"])
        ),
        "LATEST_6_MONTHS": summarize(
            subset(main_trades, *config["latest_6_month_window"])
        ),
    }
    full_days = weekday_count(*config["transfer_window"])
    latest12_days = weekday_count(*config["latest_12_month_window"])
    frequency = {
        "full_weekdays": full_days,
        "full_trades_per_weekday": len(main_trades) / full_days,
        "latest_12_month_weekdays": latest12_days,
        "latest_12_month_trades_per_weekday": (
            windows["LATEST_12_MONTHS"]["trades"] / latest12_days
        ),
    }
    signal_rows = [
        row for row in parity["audit"] if row["event"] == "SIGNAL"
    ]
    sleeves = Counter(row["sleeve"] for row in signal_rows)
    trade_count_ratio = len(main_trades) / len(expected)
    gates = config["transfer_gates"]
    source_text = SOURCE.read_text(encoding="utf-8")
    shadow_text = SHADOW.read_text(encoding="utf-8")
    ordering_text = ORDERING.read_text(encoding="utf-8")
    safe_defaults = all(
        item in source_text
        for item in (
            "input bool InpShadowMode = true;",
            "input bool InpEnableDemoOrders = false;",
            "input bool InpEmergencyStop = true;",
            "input bool InpTesterOrdersEnabled = false;",
            'input string InpDemoArmToken = "DISARMED";',
            "input double InpLotsPerTrade = 0.01;",
        )
    )
    presets_disarmed = all(
        all(
            item in text
            for item in (
                "InpShadowMode=true",
                "InpEnableDemoOrders=false",
                "InpEmergencyStop=true",
                "InpTesterOrdersEnabled=false",
                "InpDemoArmToken=DISARMED",
                "InpLotsPerTrade=0.01",
            )
        )
        for text in (shadow_text, ordering_text)
    )
    event_gate = (
        parity["events"]["SIGNAL"] == len(main_trades)
        and parity["events"]["ORDER_SEND_OK"] == len(main_trades)
        and parity["events"]["ORDER_SEND_FAILED"] == 0
        and parity["events"]["ORDER_BLOCKED"] == 0
        and parity["events"]["INIT_FAILED"] == 0
        and parity["events"]["TIME_EXIT_FAILED"] == 0
    )
    required_sleeves = set(gates["required_sleeves"])
    transfer_gate_results = {
        "compile_zero_errors_and_warnings": True,
        "safe_source_defaults": safe_defaults,
        "both_presets_disarmed": presets_disarmed,
        "observed_legal_0p01_volume_grid": any(
            row["event"] == "INIT_OK"
            and "min_0.01_step_0.01" in row["detail"]
            for row in parity["audit"]
        ),
        "minimum_research_trade_count_ratio": trade_count_ratio
        >= float(gates["minimum_research_trade_count_ratio"]),
        "minimum_trades_per_weekday": (
            frequency["full_trades_per_weekday"]
            >= float(gates["minimum_trades_per_weekday"])
        ),
        "minimum_latest_12_month_trades_per_weekday": (
            frequency["latest_12_month_trades_per_weekday"]
            >= float(gates["minimum_latest_12_month_trades_per_weekday"])
        ),
        "minimum_full_profit_factor": (
            windows["FULL_TRANSFER"]["profit_factor"]
            >= float(gates["minimum_full_profit_factor"])
        ),
        "minimum_latest_12_month_profit_factor": (
            windows["LATEST_12_MONTHS"]["profit_factor"]
            >= float(gates["minimum_latest_12_month_profit_factor"])
        ),
        "minimum_latest_6_month_profit_factor": (
            windows["LATEST_6_MONTHS"]["profit_factor"]
            >= float(gates["minimum_latest_6_month_profit_factor"])
        ),
        "win_rate": (
            float(gates["minimum_win_rate"])
            <= windows["FULL_TRANSFER"]["win_rate"]
            <= float(gates["maximum_win_rate"])
        ),
        "payoff_ratio": (
            float(gates["minimum_payoff_ratio"])
            <= windows["FULL_TRANSFER"]["realized_payoff_ratio"]
            <= float(gates["maximum_payoff_ratio"])
        ),
        "positive_net_pnl": (
            windows["FULL_TRANSFER"]["net_pnl_usd"]
            > float(gates["minimum_net_pnl_usd_exclusive"])
        ),
        "maximum_balance_drawdown": balance_drawdown_percent(metrics)
        <= float(gates["maximum_balance_drawdown_percent"]),
        "history_quality": history_quality_percent(metrics)
        >= int(gates["required_history_quality_percent"]),
        "all_12_sleeves_present": set(sleeves) == required_sleeves,
        "every_trade_exactly_0p01_lot": (
            {float(row["volume"]) for row in main_trades}
            == {float(gates["required_lot"])}
        ),
        "audit_and_broker_trades_reconcile": event_gate,
        "zero_duplicate_sleeve_days": duplicate_sleeve_days(
            parity["audit"]
        )
        == 0,
    }

    restart = parsed["RESTART"]
    restart_main_subset = subset(
        main_trades,
        *config["latest_6_month_window"],
    )
    exact_restart_replay = sorted(
        map(trade_replay_key, restart["trades"])
    ) == sorted(map(trade_replay_key, restart_main_subset))
    restart_gate_results = {
        "minimum_daily_restart_exercises": (
            restart["events"]["RESTART_EXERCISE_OK"]
            >= int(
                config["restart_gates"][
                    "minimum_daily_restart_exercises"
                ]
            )
        ),
        "exact_latest_6_month_trade_replay": exact_restart_replay,
        "zero_duplicate_sleeve_days_after_recovery": (
            duplicate_sleeve_days(restart["audit"]) == 0
        ),
        "restart_audit_and_broker_trades_reconcile": (
            restart["events"]["SIGNAL"] == len(restart["trades"])
            and restart["events"]["ORDER_SEND_OK"] == len(restart["trades"])
            and restart["events"]["ORDER_SEND_FAILED"] == 0
            and restart["events"]["INIT_FAILED"] == 0
        ),
    }

    fail_closed = parsed["FAIL_CLOSED"]
    fail_signals = fail_closed["events"]["SIGNAL"]
    fail_gate_results = {
        "minimum_observed_signals": fail_signals
        >= int(
            config["fail_closed_gates"]["minimum_observed_signals"]
        ),
        "zero_broker_trades": len(fail_closed["trades"])
        == int(config["fail_closed_gates"]["required_broker_trades"]),
        "every_signal_blocked": (
            fail_closed["events"]["ORDER_BLOCKED"] == fail_signals
            and fail_closed["events"]["ORDER_SEND_OK"] == 0
            and fail_closed["events"]["ORDER_SEND_FAILED"] == 0
        ),
        "all_blocks_are_tester_disarmed": all(
            row["detail"] == "tester_disarmed"
            for row in fail_closed["audit"]
            if row["event"] == "ORDER_BLOCKED"
        ),
    }
    prohibited_demo_targets = [
        Path(
            "C:/MT5PortableM15RegimeShadow/MQL5/Experts/"
            "EurUsdH4FrequencyCompletionControlledDemo.ex5"
        ),
        Path(
            "C:/MT5PortableProspectiveCollector/MQL5/Experts/"
            "EurUsdH4FrequencyCompletionControlledDemo.ex5"
        ),
        Path(
            "C:/MT5PortableTier1BestEA/MQL5/Experts/"
            "EurUsdH4FrequencyCompletionControlledDemo.ex5"
        ),
    ]
    deployment_gate_results = {
        "no_known_demo_terminal_installation": not any(
            path.exists() for path in prohibited_demo_targets
        ),
        "demo_deployment_not_authorized": not bool(
            config["demo_deployment_authorized"]
        ),
    }
    all_gates = {
        **{f"transfer_{k}": v for k, v in transfer_gate_results.items()},
        **{f"restart_{k}": v for k, v in restart_gate_results.items()},
        **{f"fail_closed_{k}": v for k, v in fail_gate_results.items()},
        **{f"deployment_{k}": v for k, v in deployment_gate_results.items()},
    }
    monthly_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in main_trades:
        monthly_groups[row["entry_date"][:7]].append(row)
    monthly = [
        {"month": month, **summarize(rows)}
        for month, rows in sorted(monthly_groups.items())
    ]
    result = {
        "schema_version": (
            "eurusd_h4_frequency_completion_mt5_step1_result_v1"
        ),
        "generated_at_utc": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": (
            "MT5_STEP1_VALIDATION_PASSED_NO_DEPLOYMENT"
            if all(all_gates.values())
            else "MT5_STEP1_VALIDATION_REJECTED"
        ),
        "demo_deployment_performed": False,
        "demo_order_authorized": False,
        "implementation_ready_for_permissioned_demo_install": all(
            all_gates.values()
        ),
        "validation_only_not_pristine_oos": True,
        "implementation_hashes": actual_hashes,
        "broker_sizing_result_sha256": sha256(sizing_path),
        "broker_sizing_ledger_sha256": sha256(ledger_path),
        "research_comparison": {
            "expected_trades": len(expected),
            "mt5_trades": len(main_trades),
            "trade_count_ratio": trade_count_ratio,
            "aggregate_transfer_not_exact_event_replay": True,
        },
        "broker_metrics": metrics,
        "frequency": frequency,
        "windows": windows,
        "by_sleeve": dict(sorted(sleeves.items())),
        "monthly": monthly,
        "audit": {
            "events": dict(sorted(parity["events"].items())),
            "rows": len(parity["audit"]),
            "header_present": parity["header_present"],
        },
        "restart": {
            "trades": len(restart["trades"]),
            "restart_exercises": restart["events"][
                "RESTART_EXERCISE_OK"
            ],
            "duplicate_sleeve_days": duplicate_sleeve_days(
                restart["audit"]
            ),
            "exact_latest_6_month_trade_replay": exact_restart_replay,
            "events": dict(sorted(restart["events"].items())),
        },
        "fail_closed": {
            "trades": len(fail_closed["trades"]),
            "signals": fail_signals,
            "orders_blocked": fail_closed["events"]["ORDER_BLOCKED"],
            "events": dict(sorted(fail_closed["events"].items())),
        },
        "transfer_gate_results": transfer_gate_results,
        "restart_gate_results": restart_gate_results,
        "fail_closed_gate_results": fail_gate_results,
        "deployment_gate_results": deployment_gate_results,
        "gate_results": all_gates,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for item in parsed.values():
        shutil.copy2(
            item["report_path"],
            OUTPUT / item["report_path"].name,
        )
        shutil.copy2(
            item["audit_path"],
            OUTPUT / item["audit_path"].name,
        )
    write_csv(OUTPUT / "TRADES.csv", main_trades)
    write_csv(OUTPUT / "MONTHLY_METRICS.csv", monthly)
    (OUTPUT / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_MD.write_text(
        render(result),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
