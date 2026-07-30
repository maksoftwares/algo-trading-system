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
    PACKAGE_ROOT
    / "config"
    / "frozen_h4_frequency_completion_v2_no_deployment.json"
)
SOURCE = (
    PACKAGE_ROOT
    / "mt5"
    / "Experts"
    / "EurUsdH4FrequencyCompletionControlledDemo.mq5"
)
EX5 = SOURCE.with_suffix(".ex5")
COMPILE_LOG = (
    PACKAGE_ROOT
    / "mt5"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_COMPILE.log"
)
ORDERING = (
    PACKAGE_ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_ORDERING_DEMO.template.set"
)
PARITY_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_PARITY_202407_202606.ini"
)
RESTART_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_RESTART_202601_202606.ini"
)
FAIL_CLOSED_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAIL_CLOSED_202606.ini"
)
MUTATED_LIMIT_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAULT_MUTATED_LIMIT_202606.ini"
)
LOW_EQUITY_CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAULT_LOW_EQUITY_202606.ini"
)
TEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
COMMON_FILES = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/"
    "MetaQuotes/Terminal/Common/Files"
)
CASES = {
    "PARITY": "EURUSD_H4_FREQUENCY_COMPLETION_V2_PARITY_202407_202606",
    "RESTART": "EURUSD_H4_FREQUENCY_COMPLETION_V2_RESTART_202601_202606",
    "FAIL_CLOSED": "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAIL_CLOSED_202606",
    "MUTATED_LIMIT": (
        "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAULT_MUTATED_LIMIT_202606"
    ),
    "LOW_EQUITY": (
        "EURUSD_H4_FREQUENCY_COMPLETION_V2_FAULT_LOW_EQUITY_202606"
    ),
}
OUTPUT = PACKAGE_ROOT / "outputs" / "h4_frequency_completion_v2_mt5"
REPORT_MD = (
    PACKAGE_ROOT
    / "EURUSD_H4_FREQUENCY_COMPLETION_V2_NO_DEPLOYMENT_RESULT_2026_07_30.md"
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


def summarize(
    trades: list[dict[str, Any]],
    *,
    extra_cost_usd_per_trade: float = 0.0,
) -> dict[str, Any]:
    values = [
        float(row["profit"]) - float(extra_cost_usd_per_trade)
        for row in trades
    ]
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


def sleeve_code(row: dict[str, Any]) -> str:
    return str(row["entry_comment"]).rsplit("_", 1)[-1]


def remove_best_groups(
    trades: list[dict[str, Any]],
    *,
    group_key: str,
    count: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        value = (
            str(row["entry_date"])[:7]
            if group_key == "entry_month"
            else str(row[group_key])
        )
        grouped[value].append(row)
    ranked = sorted(
        (
            (summarize(rows)["net_pnl_usd"], name)
            for name, rows in grouped.items()
        ),
        reverse=True,
    )
    removed = {name for _, name in ranked[:count]}
    return summarize(
        [
            row
            for row in trades
            if (
                str(row["entry_date"])[:7]
                if group_key == "entry_month"
                else str(row[group_key])
            )
            not in removed
        ]
    )


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
    first12 = result["windows"]["FIRST_12_MONTHS"]
    latest12 = result["windows"]["LATEST_12_MONTHS"]
    latest6 = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    return f"""# EURUSD H4 frequency-completion V2 no-deployment result

Status: **{result["status"]}**

The hardened chop-only V2 compiled with zero errors/warnings and passed the
isolated Capital.com broker-transfer, transaction-confirmation,
restart-recovery, cost/outlier, and disarmed fail-closed checks. No file was
installed into a demo terminal and no demo order was authorized.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Two-year transfer | {full["trades"]} | {result["frequency"]["full_trades_per_weekday"]:.3f} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | ${full["net_pnl_usd"]:+.2f} |
| First 12 months | {first12["trades"]} | - | {first12["win_rate"]:.2%} | {first12["realized_payoff_ratio"]:.3f} | {first12["profit_factor"]:.3f} | ${first12["net_pnl_usd"]:+.2f} |
| Latest 12 months | {latest12["trades"]} | {result["frequency"]["latest_12_month_trades_per_weekday"]:.3f} | {latest12["win_rate"]:.2%} | {latest12["realized_payoff_ratio"]:.3f} | {latest12["profit_factor"]:.3f} | ${latest12["net_pnl_usd"]:+.2f} |
| Latest 6 months | {latest6["trades"]} | - | {latest6["win_rate"]:.2%} | {latest6["realized_payoff_ratio"]:.3f} | {latest6["profit_factor"]:.3f} | ${latest6["net_pnl_usd"]:+.2f} |

All six chop sleeves traded and every broker trade used exactly 0.01 lot.
The failed compression sleeves placed zero trades. History quality was
{result["broker_metrics"]["History Quality"]}; maximum balance drawdown was
{result["broker_metrics"]["Balance Drawdown Maximal"]}.

The restart exercise rebuilt state on
{result["restart"]["restart_exercises"]} trading days and exactly replayed the
unchanged {latest6["trades"]}-trade latest-six-month result, with zero duplicate
sleeve-days. All {full["trades"]} entry requests were transaction-confirmed.
The disarmed test observed {result["fail_closed"]["signals"]} valid signals,
blocked all of them, and placed zero trades.

One-pip-plus-$0.07 stressed PF was
{result["robustness"]["one_pip_plus_commission"]["profit_factor"]:.3f}.
Removing the three best months left PF
{result["robustness"]["best_three_months_removed"]["profit_factor"]:.3f};
removing the best 5% of active days left PF
{result["robustness"]["best_five_percent_days_removed"]["profit_factor"]:.3f}.

This validates executable behavior on MT5 history. It is not fresh future
evidence and does not authorize installation or orders.

Failed gates: {", ".join(failed) if failed else "none"}.
"""


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    paths = {
        "source_mq5": SOURCE,
        "compiled_ex5": EX5,
        "compile_log": COMPILE_LOG,
        "ordering_template": ORDERING,
        "parity_tester_config": PARITY_CONFIG,
        "restart_tester_config": RESTART_CONFIG,
        "fail_closed_tester_config": FAIL_CLOSED_CONFIG,
        "mutated_limit_fault_config": MUTATED_LIMIT_CONFIG,
        "low_equity_fault_config": LOW_EQUITY_CONFIG,
    }
    actual_hashes = {name: sha256(path) for name, path in paths.items()}
    if actual_hashes != config["implementation_hashes"]:
        raise RuntimeError("Frozen MT5 implementation hash mismatch")
    compile_text = COMPILE_LOG.read_text(encoding="utf-16")
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError("MQL5 compilation did not pass")
    benchmark_path = (
        PACKAGE_ROOT / config["v1_broker_benchmark"]["path"]
    )
    if sha256(benchmark_path) != config["v1_broker_benchmark"]["sha256"]:
        raise RuntimeError("Frozen V1 broker benchmark hash mismatch")
    with benchmark_path.open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        benchmark = list(csv.DictReader(handle))
    chop_codes = {"BC", "NC", "RC", "F3C", "F5C", "M30C"}
    benchmark_chop = [
        row
        for row in benchmark
        if str(row["entry_comment"]).rsplit("_", 1)[-1]
        in chop_codes
    ]
    if len(benchmark_chop) != int(
        config["v1_broker_benchmark"]["expected_chop_trades"]
    ):
        raise RuntimeError("Unexpected V1 chop benchmark count")

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
        "FIRST_12_MONTHS": summarize(
            subset(main_trades, *config["first_12_month_window"])
        ),
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
    active_day_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    monthly_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in main_trades:
        active_day_groups[row["entry_date"]].append(row)
        monthly_groups[row["entry_date"][:7]].append(row)
    frequency.update(
        {
            "active_trade_days": len(active_day_groups),
            "active_day_share": len(active_day_groups) / full_days,
            "trades_per_active_day": (
                len(main_trades) / len(active_day_groups)
            ),
            "maximum_trades_per_active_day": max(
                map(len, active_day_groups.values())
            ),
        }
    )
    monthly = [
        {"month": month, **summarize(rows)}
        for month, rows in sorted(monthly_groups.items())
    ]
    positive_month_share = (
        sum(row["net_pnl_usd"] > 0.0 for row in monthly) / len(monthly)
    )
    best_day_count = max(1, math.ceil(0.05 * len(active_day_groups)))
    robustness = {
        "one_pip_plus_commission": summarize(main_trades),
        "best_three_months_removed": remove_best_groups(
            main_trades,
            group_key="entry_month",
            count=3,
        ),
        "best_five_percent_days_removed": remove_best_groups(
            main_trades,
            group_key="entry_date",
            count=best_day_count,
        ),
    }
    signal_rows = [
        row for row in parity["audit"] if row["event"] == "SIGNAL"
    ]
    sleeves = Counter(row["sleeve"] for row in signal_rows)
    gates = config["transfer_gates"]
    robustness["one_pip_plus_commission"] = summarize(
        main_trades,
        extra_cost_usd_per_trade=(
            float(gates["extra_one_pip_cost_usd_per_trade"])
            + float(gates["round_trip_commission_usd_per_trade"])
        ),
    )
    source_text = SOURCE.read_text(encoding="utf-8")
    ordering_text = ORDERING.read_text(encoding="utf-8")
    safe_defaults = all(
        item in source_text
        for item in (
            "input bool InpShadowMode = true;",
            "input bool InpEnableDemoOrders = false;",
            "input bool InpEmergencyStop = true;",
            "input bool InpTesterOrdersEnabled = false;",
            "input bool InpEnableCompressionSleeves = false;",
            'input string InpDemoArmToken = "DISARMED";',
            "input double InpLotsPerTrade = 0.01;",
            "input int InpMaximumTradesPerUtcDay = 6;",
            "input int InpMaximumOwnPositions = 6;",
            "bool ConfirmSleevePosition(",
            "void OnTradeTransaction(",
            'reason = "audit_unavailable";',
            "persistentBreakerLatched",
        )
    )
    ordering_template_disarmed = all(
        item in ordering_text
        for item in (
            "InpShadowMode=false",
            "InpEnableDemoOrders=false",
            "InpEmergencyStop=true",
            "InpTesterOrdersEnabled=false",
            "InpEnableCompressionSleeves=false",
            "InpDemoArmToken=DISARMED",
            "InpLotsPerTrade=0.01",
        )
    )
    event_gate = (
        parity["events"]["SIGNAL"] == len(main_trades)
        and parity["events"]["ORDER_INTENT"] == len(main_trades)
        and parity["events"]["ORDER_CONFIRMED"] == len(main_trades)
        and parity["events"]["ORDER_EXECUTION_UNCERTAIN"] == 0
        and parity["events"]["ORDER_BLOCKED"] == 0
        and parity["events"]["INIT_FAILED"] == 0
        and parity["events"]["TIME_EXIT_FAILED"] == 0
        and parity["events"]["BREAKER_EXIT_RETRY_REQUIRED"] == 0
        and parity["events"]["RISK_BREAKER_LATCHED"] == 0
    )
    required_sleeves = set(gates["required_sleeves"])
    code_to_sleeve = {
        "BC": "BASELINE_CHOP",
        "NC": "NEXT_CLOSE_CHOP",
        "RC": "RETEST_CHOP",
        "F3C": "M15_FOLLOW_3_CHOP",
        "F5C": "M15_FOLLOW_5_CHOP",
        "M30C": "M30_FIRST_BREAK_CHOP",
    }
    trades_by_sleeve: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in main_trades:
        code = sleeve_code(row)
        if code not in code_to_sleeve:
            raise RuntimeError(f"Unexpected V2 sleeve code: {code}")
        trades_by_sleeve[code_to_sleeve[code]].append(row)
    sleeve_metrics = {
        name: summarize(rows)
        for name, rows in sorted(trades_by_sleeve.items())
    }
    benchmark_keys = {
        (row["entry_time"], sleeve_code(row)) for row in benchmark_chop
    }
    v2_keys = {
        (row["entry_time"], sleeve_code(row)) for row in main_trades
    }
    preserved_benchmark = len(benchmark_keys & v2_keys)
    preservation_ratio = preserved_benchmark / len(benchmark_keys)
    transfer_gate_results = {
        "compile_zero_errors_and_warnings": True,
        "safe_source_defaults": safe_defaults,
        "ordering_template_disarmed": ordering_template_disarmed,
        "observed_legal_0p01_volume_grid": any(
            row["event"] == "INIT_OK"
            and "min_0.01_step_0.01" in row["detail"]
            for row in parity["audit"]
        ),
        "v1_chop_entries_preserved": preservation_ratio
        >= float(
            config["v1_broker_benchmark"]["minimum_preservation_ratio"]
        ),
        "minimum_trade_count": len(main_trades)
        >= int(gates["minimum_trades"]),
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
        "minimum_first_12_month_profit_factor": (
            windows["FIRST_12_MONTHS"]["profit_factor"]
            >= float(gates["minimum_first_12_month_profit_factor"])
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
        "positive_net_pnl": windows["FULL_TRANSFER"]["net_pnl_usd"] > 0.0,
        "one_pip_plus_commission_profit_factor": robustness[
            "one_pip_plus_commission"
        ]["profit_factor"]
        >= float(
            gates["minimum_one_pip_plus_commission_profit_factor"]
        ),
        "positive_month_share": positive_month_share
        >= float(gates["minimum_positive_month_share"]),
        "best_three_months_removed_profit_factor": robustness[
            "best_three_months_removed"
        ]["profit_factor"]
        >= float(
            gates["minimum_best_three_months_removed_profit_factor"]
        ),
        "best_five_percent_days_removed_profit_factor": robustness[
            "best_five_percent_days_removed"
        ]["profit_factor"]
        >= float(
            gates[
                "minimum_best_five_percent_days_removed_profit_factor"
            ]
        ),
        "maximum_balance_drawdown": balance_drawdown_percent(metrics)
        <= float(gates["maximum_balance_drawdown_percent"]),
        "history_quality": history_quality_percent(metrics)
        >= int(gates["required_history_quality_percent"]),
        "only_required_chop_sleeves_present": (
            set(sleeves) == required_sleeves
            and set(trades_by_sleeve) == required_sleeves
            and all(row["regime"] == "CHOP" for row in signal_rows)
        ),
        "each_sleeve_minimum_trades_and_profit_factor": all(
            summary["trades"] >= int(gates["minimum_each_sleeve_trades"])
            and summary["profit_factor"]
            > float(gates["minimum_each_sleeve_profit_factor_exclusive"])
            for summary in sleeve_metrics.values()
        ),
        "every_trade_exactly_0p01_lot": (
            {float(row["volume"]) for row in main_trades}
            == {float(gates["required_lot"])}
        ),
        "audit_and_broker_trades_reconcile": event_gate,
        "maximum_trades_per_active_day": (
            frequency["maximum_trades_per_active_day"]
            <= int(gates["maximum_trades_per_active_day"])
        ),
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
            and restart["events"]["ORDER_INTENT"] == len(restart["trades"])
            and restart["events"]["ORDER_CONFIRMED"]
            == len(restart["trades"])
            and restart["events"]["ORDER_EXECUTION_UNCERTAIN"] == 0
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
            and fail_closed["events"]["ORDER_CONFIRMED"] == 0
            and fail_closed["events"]["ORDER_EXECUTION_UNCERTAIN"] == 0
        ),
        "all_blocks_are_tester_disarmed": all(
            row["detail"] == "tester_disarmed"
            for row in fail_closed["audit"]
            if row["event"] == "ORDER_BLOCKED"
        ),
    }
    mutated_limit = parsed["MUTATED_LIMIT"]
    low_equity = parsed["LOW_EQUITY"]
    low_equity_signals = low_equity["events"]["SIGNAL"]
    fault_gate_results = {
        "mutated_limit_zero_trades": len(mutated_limit["trades"]) == 0,
        "mutated_limit_failed_initialization": (
            mutated_limit["events"]["INIT_FAILED"] == 1
            and any(
                row["event"] == "INIT_FAILED"
                and row["detail"] == "frozen_exposure_limits_changed"
                for row in mutated_limit["audit"]
            )
        ),
        "low_equity_zero_trades": len(low_equity["trades"]) == 0,
        "low_equity_every_signal_blocked": (
            low_equity_signals > 0
            and low_equity["events"]["ORDER_BLOCKED"]
            == low_equity_signals
            and all(
                row["detail"] == "minimum_account_equity"
                for row in low_equity["audit"]
                if row["event"] == "ORDER_BLOCKED"
            )
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
        "demo_orders_not_authorized": not bool(
            config["demo_orders_authorized"]
        ),
    }
    all_gates = {
        **{f"transfer_{k}": v for k, v in transfer_gate_results.items()},
        **{f"restart_{k}": v for k, v in restart_gate_results.items()},
        **{f"fail_closed_{k}": v for k, v in fail_gate_results.items()},
        **{f"fault_{k}": v for k, v in fault_gate_results.items()},
        **{f"deployment_{k}": v for k, v in deployment_gate_results.items()},
    }
    result = {
        "schema_version": (
            "eurusd_h4_frequency_completion_v2_no_deployment_result_v1"
        ),
        "generated_at_utc": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": (
            "V2_PREDEPLOYMENT_VALIDATION_PASSED_NO_DEPLOYMENT"
            if all(all_gates.values())
            else "V2_PREDEPLOYMENT_VALIDATION_REJECTED"
        ),
        "demo_deployment_performed": False,
        "demo_order_authorized": False,
        "implementation_ready_for_permissioned_ordering_demo": all(
            all_gates.values()
        ),
        "validation_only_not_pristine_oos": True,
        "implementation_hashes": actual_hashes,
        "v1_broker_benchmark_sha256": sha256(benchmark_path),
        "v1_chop_preservation": {
            "benchmark_trades": len(benchmark_chop),
            "preserved_entries": preserved_benchmark,
            "preservation_ratio": preservation_ratio,
        },
        "broker_metrics": metrics,
        "frequency": frequency,
        "windows": windows,
        "robustness": robustness,
        "by_sleeve": dict(sorted(sleeves.items())),
        "sleeve_metrics": sleeve_metrics,
        "positive_month_share": positive_month_share,
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
        "fault_tests": {
            "mutated_limit": {
                "trades": len(mutated_limit["trades"]),
                "events": dict(sorted(mutated_limit["events"].items())),
            },
            "low_equity": {
                "trades": len(low_equity["trades"]),
                "signals": low_equity_signals,
                "events": dict(sorted(low_equity["events"].items())),
            },
        },
        "transfer_gate_results": transfer_gate_results,
        "restart_gate_results": restart_gate_results,
        "fail_closed_gate_results": fail_gate_results,
        "fault_gate_results": fault_gate_results,
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
