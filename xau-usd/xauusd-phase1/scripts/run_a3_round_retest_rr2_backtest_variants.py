from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from run_xau_920101_breakout_retest_backtest_variants import (
    copy_include_tree,
    parse_mt5_report,
    read_log_rows,
    read_text,
    require_file,
    safe_name,
    stop_backtest_terminal,
    summarize_orders,
    summarize_trades,
    wait_for_file,
    write_dict_rows,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EXPERTS_SOURCE_ROOT = PHASE1_ROOT / "mt5" / "Experts"
INCLUDE_SOURCE = PHASE1_ROOT / "mt5" / "Include"
DEFAULT_BACKTEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_METAEDITOR = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_DIR = PHASE1_ROOT / "outputs" / "reports" / "mt5_backtests"
DEFAULT_FROM_DATE = "2022.07.01"
DEFAULT_TO_DATE = "2026.06.30"
DEFAULT_TAG = "OWNER_GOAL_A3_RD_202207_202606"

ACCOUNT_LOGIN = "1025742"
ACCOUNT_SERVER = "Capital.ComMena-Demo"


@dataclass(frozen=True)
class Variant:
    name: str
    label: str
    note: str
    ea_name: str
    tester_inputs: dict[str, str]


VARIANTS = [
    Variant(
        name="rdguard_raw_r20_cost030",
        label="RDGUARD raw round-retest, 2.0R, cost <=0.30R",
        note="Impulse veto disabled to measure base pattern frequency and shape.",
        ea_name="Account3RoundRetestGuardedExecutor",
        tester_inputs={
            "InpMagicNumber": "933010",
            "InpOrderComment": "RDG_RAW_R20",
            "InpImpulseVetoThreshold": "-999.0",
            "InpTargetR": "2.0",
            "InpMaxEstimatedCostR": "0.30",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
    Variant(
        name="rdguard_default_r20_cost030",
        label="RDGUARD default impulse veto, 2.0R, cost <=0.30R",
        note="Default guarded shape at the owner minimum payoff target.",
        ea_name="Account3RoundRetestGuardedExecutor",
        tester_inputs={
            "InpMagicNumber": "933011",
            "InpOrderComment": "RDG_DEF_R20",
            "InpImpulseVetoThreshold": "-1.5",
            "InpTargetR": "2.0",
            "InpMaxEstimatedCostR": "0.30",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
    Variant(
        name="rdguard_default_r25_cost030",
        label="RDGUARD default impulse veto, 2.5R, cost <=0.30R",
        note="Checks whether stretching payoff creates a useful W/L tradeoff.",
        ea_name="Account3RoundRetestGuardedExecutor",
        tester_inputs={
            "InpMagicNumber": "933012",
            "InpOrderComment": "RDG_DEF_R25",
            "InpImpulseVetoThreshold": "-1.5",
            "InpTargetR": "2.5",
            "InpMaxEstimatedCostR": "0.30",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
    Variant(
        name="rdguard_default_r20_cost015",
        label="RDGUARD default impulse veto, 2.0R, cost <=0.15R",
        note="Strict cost gate; tests whether high-cost retests are the main damage source.",
        ea_name="Account3RoundRetestGuardedExecutor",
        tester_inputs={
            "InpMagicNumber": "933013",
            "InpOrderComment": "RDG_DEF_R20_C15",
            "InpImpulseVetoThreshold": "-1.5",
            "InpTargetR": "2.0",
            "InpMaxEstimatedCostR": "0.15",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
    Variant(
        name="rdstruct_default_r20_cost030",
        label="RDSTRUCT M15 structure confirmation, 2.0R, cost <=0.30R",
        note="Existing M15 structure filter at the owner minimum payoff target.",
        ea_name="Account3RoundRetestStructuredExecutor",
        tester_inputs={
            "InpMagicNumber": "933110",
            "InpOrderComment": "RDS_DEF_R20",
            "InpTargetR": "2.0",
            "InpMaxEstimatedCostR": "0.30",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
    Variant(
        name="rdstruct_default_r25_cost030",
        label="RDSTRUCT M15 structure confirmation, 2.5R, cost <=0.30R",
        note="Structured retest with stretched payoff.",
        ea_name="Account3RoundRetestStructuredExecutor",
        tester_inputs={
            "InpMagicNumber": "933111",
            "InpOrderComment": "RDS_DEF_R25",
            "InpTargetR": "2.5",
            "InpMaxEstimatedCostR": "0.30",
            "InpAbsoluteRejectCostR": "0.30",
        },
    ),
]


COMMON_TESTER_INPUTS = {
    "InpRunId": "BT_A3_RD_RR2",
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpTargetSymbol": "XAUUSD",
    "InpExpectedServerMarker": "Demo",
    "InpAllowedAccountLoginsCsv": ACCOUNT_LOGIN,
    "InpExecutionKillSwitchFileName": "nonexistent_a3_rd_rr2_exec_kill.txt",
    "InpFullStopFileName": "nonexistent_a3_rd_rr2_full_stop.txt",
    "InpDirectionStateFileName": "nonexistent_a3_rd_rr2_direction_state.csv",
    "InpStreakLossCount": "999",
    "InpStreakWindowMinutes": "120",
    "InpDailyLossStopAed": "-999999.0",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxMeasuredSpreadPoints": "75.0",
    "InpMinSecondsBetweenOrders": "0",
    "InpFixedLot": "0.01",
    "InpDeviationPoints": "50",
}


def run_variants(
    backtest_root: Path = DEFAULT_BACKTEST_ROOT,
    metaeditor: Path = DEFAULT_METAEDITOR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    from_date: str = DEFAULT_FROM_DATE,
    to_date: str = DEFAULT_TO_DATE,
    tag: str = DEFAULT_TAG,
    report_md: Path | None = None,
    report_json: Path | None = None,
    variant_names: set[str] | None = None,
    variant_timeout_seconds: int = 900,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> dict[str, Any]:
    backtest_root = backtest_root.resolve()
    output_dir = output_dir.resolve()
    terminal = backtest_root / "terminal64.exe"
    require_file(INCLUDE_SOURCE)
    require_file(terminal)
    require_file(metaeditor)

    selected_variants = [variant for variant in VARIANTS if variant_names is None or variant.name in variant_names]
    if not selected_variants:
        available = ", ".join(variant.name for variant in VARIANTS)
        raise ValueError(f"No variants selected. Available variants: {available}")

    required_eas = sorted({variant.ea_name for variant in selected_variants})
    compile_logs = compile_eas(backtest_root, metaeditor, required_eas)
    safe_tag = safe_name(tag)
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    variant_dir = output_dir / f"a3_round_retest_rr2_{safe_tag.lower()}_{run_stamp}"
    variant_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for variant in selected_variants:
        results.append(
            run_variant(
                backtest_root,
                terminal,
                variant,
                variant_dir,
                from_date,
                to_date,
                safe_tag,
                variant_timeout_seconds,
                deposit,
                currency,
            )
        )

    report_md = report_md or PHASE1_ROOT / "outputs" / "reports" / f"A3_ROUND_RETEST_RR2_MT5_PROBE_{safe_tag}.md"
    report_json = report_json or report_md.with_suffix(".json")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "family": "A3 round-retest RR2 probe",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "period": f"{from_date} -> {to_date}",
            "account_context": f"{ACCOUNT_LOGIN} / {ACCOUNT_SERVER}",
            "tester_deposit": deposit,
            "tester_currency": currency,
            "terminal_sandbox": str(backtest_root),
            "model": "MT5 Strategy Tester / every tick / history quality from report",
            "no_live_runtime_change": True,
            "variant_count": len(selected_variants),
            "selected_variants": [variant.name for variant in selected_variants],
            "anti_overfit_boundary": "Six preregistered variants only; no optimizer or post-hoc threshold search.",
            "review_spend_rule": "Ask for review only if a variant reaches WR >= 50% and avg_win/avg_loss >= 2.0.",
        },
        "compile_logs": {name: str(path) for name, path in compile_logs.items()},
        "variants": results,
        "winner": choose_winner(results),
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def compile_eas(backtest_root: Path, metaeditor: Path, ea_names: list[str]) -> dict[str, Path]:
    mql5_root = backtest_root / "MQL5"
    experts = mql5_root / "Experts"
    include_target = mql5_root / "Include"
    experts.mkdir(parents=True, exist_ok=True)
    include_target.mkdir(parents=True, exist_ok=True)
    copy_include_tree(INCLUDE_SOURCE, include_target)

    logs: dict[str, Path] = {}
    for ea_name in ea_names:
        source = EXPERTS_SOURCE_ROOT / f"{ea_name}.mq5"
        require_file(source)
        shutil.copy2(source, experts / f"{ea_name}.mq5")
        log = backtest_root / "Logs" / f"compile_{ea_name}_a3_rd_rr2_20260705.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [str(metaeditor), f"/compile:{experts / f'{ea_name}.mq5'}", f"/log:{log}"],
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        ex5 = experts / f"{ea_name}.ex5"
        if not ex5.exists():
            raise RuntimeError(f"MetaEditor did not produce EX5 for {ea_name}. Log:\n{read_text(log)}")
        log_text = read_text(log).lower()
        if "error(s)" in log_text and "0 error(s)" not in log_text:
            raise RuntimeError(f"MetaEditor compile reported errors for {ea_name}:\n{read_text(log)}")
        logs[ea_name] = log
    return logs


def run_variant(
    backtest_root: Path,
    terminal: Path,
    variant: Variant,
    variant_dir: Path,
    from_date: str,
    to_date: str,
    tag: str,
    timeout_seconds: int = 900,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> dict[str, Any]:
    report_base = f"A3RoundRetestRR2_{tag}_M5_{variant.name}"
    startup_log = f"a3_rd_rr2_bt_{variant.name}_startup.csv"
    signal_log = f"a3_rd_rr2_bt_{variant.name}_signal.csv"
    order_log = f"a3_rd_rr2_bt_{variant.name}_order.csv"
    config = write_config(
        backtest_root,
        variant,
        report_base,
        startup_log,
        signal_log,
        order_log,
        from_date,
        to_date,
        tag,
        deposit,
        currency,
    )
    remove_old_variant_files(backtest_root, report_base, startup_log, signal_log, order_log)
    stop_backtest_terminal(terminal)
    proc = subprocess.Popen(
        [str(terminal), "/portable", f"/config:{config}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    html_report = backtest_root / "Reports" / f"{report_base}.htm"
    timed_out = False
    timeout_error = ""
    try:
        wait_for_file(html_report, timeout_seconds=timeout_seconds)
        time.sleep(2)
    except TimeoutError as exc:
        timed_out = True
        timeout_error = str(exc)
    finally:
        stop_backtest_terminal(terminal)

    stdout_tail = ""
    stderr_tail = ""
    returncode = None
    try:
        stdout, stderr = proc.communicate(timeout=5)
        stdout_tail = stdout[-1000:] if stdout else ""
        stderr_tail = stderr[-1000:] if stderr else ""
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
        stdout_tail = stdout[-1000:] if stdout else ""
        stderr_tail = stderr[-1000:] if stderr else ""
        returncode = proc.returncode

    if timed_out:
        result = {
            "name": variant.name,
            "label": variant.label,
            "note": variant.note,
            "ea_name": variant.ea_name,
            "tester_inputs": {
                **COMMON_TESTER_INPUTS,
                **variant.tester_inputs,
            },
            "config": str(config),
            "html_report": str(html_report),
            "trade_csv": "",
            "signal_csv": "",
            "order_csv": "",
            "summary_json": str(variant_dir / f"{report_base}_summary.json"),
            "mt5_report_metrics": {},
            "summary": {"overall": {}},
            "goal_metrics": empty_goal_metrics(from_date, to_date),
            "signal_activity": {"rows": 0, "would_signal_rows": 0, "guard_pass_rows": 0},
            "order_activity": {"rows": 0, "actions": {}, "top_guard_reasons": {}, "top_signal_reasons": {}},
            "terminal_returncode": returncode,
            "terminal_stdout_tail": stdout_tail,
            "terminal_stderr_tail": stderr_tail,
            "status": "TIMEOUT_NO_REPORT",
            "error": timeout_error,
        }
        Path(result["summary_json"]).write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    trades, metrics = parse_mt5_report(html_report)
    signals = read_log_rows(backtest_root, signal_log)
    orders = read_log_rows(backtest_root, order_log)
    summary = summarize_trades(trades)
    goal = compute_goal_metrics(trades, from_date, to_date)
    signal_summary = summarize_signals(signals)
    order_summary = summarize_orders(orders)

    trade_csv = variant_dir / f"{report_base}_trades.csv"
    signal_csv = variant_dir / f"{report_base}_signals.csv"
    order_csv = variant_dir / f"{report_base}_orders.csv"
    summary_json = variant_dir / f"{report_base}_summary.json"
    write_dict_rows(trade_csv, trades)
    write_dict_rows(signal_csv, signals)
    write_dict_rows(order_csv, orders)
    result = {
        "name": variant.name,
        "label": variant.label,
        "note": variant.note,
        "ea_name": variant.ea_name,
        "tester_inputs": {
            **COMMON_TESTER_INPUTS,
            **variant.tester_inputs,
        },
        "config": str(config),
        "html_report": str(html_report),
        "trade_csv": str(trade_csv),
        "signal_csv": str(signal_csv),
        "order_csv": str(order_csv),
        "summary_json": str(summary_json),
        "mt5_report_metrics": metrics,
        "summary": summary,
        "goal_metrics": goal,
        "signal_activity": signal_summary,
        "order_activity": order_summary,
        "terminal_returncode": returncode,
        "terminal_stdout_tail": stdout_tail,
        "terminal_stderr_tail": stderr_tail,
    }
    summary_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def write_config(
    backtest_root: Path,
    variant: Variant,
    report_base: str,
    startup_log: str,
    signal_log: str,
    order_log: str,
    from_date: str,
    to_date: str,
    tag: str,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> Path:
    inputs = {
        **COMMON_TESTER_INPUTS,
        **variant.tester_inputs,
        "InpRunId": f"BT_A3_RD_RR2_{safe_name(tag)}_{variant.name.upper()}",
        "InpStartupLogFileName": startup_log,
        "InpSignalLogFileName": signal_log,
        "InpOrderLogFileName": order_log,
    }
    lines = [
        "[Common]",
        f"Login={ACCOUNT_LOGIN}",
        f"Server={ACCOUNT_SERVER}",
        "KeepPrivate=1",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={variant.ea_name}.ex5",
        "Symbol=XAUUSD",
        "Period=M5",
        "Optimization=0",
        "Model=0",
        "Dates=2",
        f"FromDate={from_date}",
        f"ToDate={to_date}",
        "ForwardMode=0",
        f"Deposit={deposit}",
        f"Currency={currency}",
        "ProfitInPips=0",
        "Leverage=200",
        "ExecutionMode=0",
        "OptimizationCriterion=0",
        "Visual=0",
        f"Report=Reports\\{report_base}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "",
        "[TesterInputs]",
    ]
    lines.extend(f"{key}={value}" for key, value in inputs.items())
    config = backtest_root / "Config" / f"{report_base}.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config


def remove_old_variant_files(backtest_root: Path, report_base: str, *log_names: str) -> None:
    for suffix in [".htm", ".png", "-holding.png", "-mfemae.png", "-hst.png"]:
        path = backtest_root / "Reports" / f"{report_base}{suffix}"
        if path.exists():
            path.unlink()
    files_root = backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    for name in log_names:
        path = files_root / name
        if path.exists():
            path.unlink()


def compute_goal_metrics(trades: list[dict[str, Any]], from_date: str, to_date: str) -> dict[str, Any]:
    profits = [float(trade["profit_aed"]) for trade in trades]
    wins = [value for value in profits if value > 0]
    losses = [-value for value in profits if value < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    total = sum(profits)
    count = len(profits)
    active_days = {str(trade["date"]) for trade in trades}
    trading_days = trading_weekday_count(parse_mt5_date(from_date), parse_mt5_date(to_date))
    win_rate = (len(wins) / count * 100.0) if count else 0.0
    avg_win = (gross_profit / len(wins)) if wins else 0.0
    avg_loss = (gross_loss / len(losses)) if losses else 0.0
    wl_ratio = (avg_win / avg_loss) if avg_loss else None
    active_day_pct = (len(active_days) / trading_days * 100.0) if trading_days else 0.0
    return {
        "trades": count,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "avg_win_aed": round(avg_win, 2),
        "avg_loss_aed": round(avg_loss, 2),
        "avg_win_loss_ratio": round(wl_ratio, 4) if wl_ratio is not None else None,
        "manual_pnl_aed": round(total, 2),
        "gross_profit_aed": round(gross_profit, 2),
        "gross_loss_aed": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "active_entry_days": len(active_days),
        "trading_weekdays_in_window": trading_days,
        "active_day_pct": round(active_day_pct, 2),
        "owner_core_shape_pass": bool(count and win_rate >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0),
        "owner_daily_frequency_pass": active_day_pct >= 90.0,
        "owner_goal_pass": bool(count and win_rate >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0 and active_day_pct >= 90.0),
    }


def empty_goal_metrics(from_date: str, to_date: str) -> dict[str, Any]:
    trading_days = trading_weekday_count(parse_mt5_date(from_date), parse_mt5_date(to_date))
    return {
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate_pct": 0.0,
        "avg_win_aed": 0.0,
        "avg_loss_aed": 0.0,
        "avg_win_loss_ratio": None,
        "manual_pnl_aed": 0.0,
        "gross_profit_aed": 0.0,
        "gross_loss_aed": 0.0,
        "profit_factor": None,
        "active_entry_days": 0,
        "trading_weekdays_in_window": trading_days,
        "active_day_pct": 0.0,
        "owner_core_shape_pass": False,
        "owner_daily_frequency_pass": False,
        "owner_goal_pass": False,
    }


def summarize_signals(rows: list[dict[str, str]]) -> dict[str, Any]:
    would_signal_rows = [row for row in rows if lower_bool(row.get("would_signal"))]
    guard_pass_rows = [row for row in rows if lower_bool(row.get("guard_pass"))]
    signal_days = {row.get("m5_bar_time", "")[:10] for row in would_signal_rows if row.get("m5_bar_time")}
    pass_days = {row.get("m5_bar_time", "")[:10] for row in guard_pass_rows if row.get("m5_bar_time")}
    return {
        "rows": len(rows),
        "would_signal_rows": len(would_signal_rows),
        "guard_pass_rows": len(guard_pass_rows),
        "would_signal_days": len(signal_days),
        "guard_pass_days": len(pass_days),
        "top_reason_codes": dict(Counter(row.get("reason_code", "") for row in rows).most_common(12)),
        "top_guard_reasons": dict(Counter(row.get("guard_reason", "") for row in rows).most_common(12)),
    }


def choose_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"status": "NO_RESULTS"}
    full_hits = [result for result in results if result["goal_metrics"]["owner_goal_pass"]]
    core_hits = [result for result in results if result["goal_metrics"]["owner_core_shape_pass"]]
    if full_hits:
        best = max(full_hits, key=lambda result: result["goal_metrics"]["manual_pnl_aed"])
        return {
            "status": "OWNER_GOAL_HIT_REVIEW_REQUIRED",
            "best_variant": best["name"],
            "review_recommendation": "Spend reviewer only after packaging source diffs, configs, reports, and ledgers.",
        }
    if core_hits:
        best = max(core_hits, key=lambda result: result["goal_metrics"]["active_day_pct"])
        return {
            "status": "CORE_WR_WL_SHAPE_HIT_FREQUENCY_GAP",
            "best_variant": best["name"],
            "review_recommendation": "Consider review only if the activity gap is realistically bridgeable by a preregistered portfolio layer.",
        }
    near = [
        result
        for result in results
        if result["goal_metrics"]["win_rate_pct"] >= 48.0
        and (result["goal_metrics"]["avg_win_loss_ratio"] or 0.0) >= 1.8
    ]
    best = max(results, key=goal_score)
    return {
        "status": "NO_OWNER_GOAL_HIT",
        "best_by_goal_score": best["name"],
        "near_core_count": len(near),
        "review_recommendation": "Do not spend reviewer; continue discovery.",
    }


def goal_score(result: dict[str, Any]) -> float:
    metrics = result["goal_metrics"]
    wr = min(metrics["win_rate_pct"] / 50.0, 1.2)
    wl = min((metrics["avg_win_loss_ratio"] or 0.0) / 2.0, 1.2)
    active = min(metrics["active_day_pct"] / 90.0, 1.2)
    pf = min((metrics["profit_factor"] or 0.0) / 1.25, 1.2)
    return wr + wl + active + pf


def render_markdown(payload: dict[str, Any]) -> str:
    currency = payload.get("scope", {}).get("tester_currency", "AED")
    lines = [
        "# A3 Round-Retest RR2 MT5 Probe",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Period: `{payload['scope']['period']}`",
        f"Tester: `{payload['scope']['account_context']}`",
        f"Sandbox: `{payload['scope']['terminal_sandbox']}`",
        f"Winner status: `{payload['winner']['status']}`",
        f"Review recommendation: `{payload['winner'].get('review_recommendation', 'n/a')}`",
        "",
        "## Fixed Boundary",
        "",
        "- Exact MT5 Strategy Tester only; no live/demo runtime attachment.",
        "- Six preregistered variants only; no optimizer or threshold sweep.",
        "- PnL and WR/W-L metrics below are recomputed from parsed deal rows, not copied from the MT5 summary.",
        "",
        "## Results",
        "",
        "| Variant | EA | Trades | WR % | Avg W | Avg L | W/L | Active Days % | PF | Manual PnL | Goal |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in payload["variants"]:
        goal = result["goal_metrics"]
        goal_text = "PASS" if goal["owner_goal_pass"] else "CORE_ONLY" if goal["owner_core_shape_pass"] else "MISS"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{result['name']}`",
                    f"`{result['ea_name']}`",
                    str(goal["trades"]),
                    f"{goal['win_rate_pct']:.2f}",
                    money(goal["avg_win_aed"], currency),
                    money(goal["avg_loss_aed"], currency),
                    format_ratio(goal["avg_win_loss_ratio"]),
                    f"{goal['active_day_pct']:.2f}",
                    format_ratio(goal["profit_factor"]),
                    money(goal["manual_pnl_aed"], currency),
                    f"`{goal_text}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Variant Notes",
            "",
        ]
    )
    for result in payload["variants"]:
        goal = result["goal_metrics"]
        signals = result["signal_activity"]
        orders = result["order_activity"]
        mt5_total_profit = result.get("mt5_report_metrics", {}).get("Total Net Profit", "n/a")
        equity_dd = result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal", "n/a")
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"- Label: {result['label']}",
                f"- Note: {result['note']}",
                f"- Status: `{result.get('status', 'COMPLETED')}`.",
                f"- Manual PnL: `{money(goal['manual_pnl_aed'], currency)}`; MT5 summary net profit cross-check: `{mt5_total_profit}`.",
                f"- MT5 equity drawdown maximal: `{equity_dd}`.",
                f"- Signals: `{signals['would_signal_rows']}` would-signal rows, `{signals['guard_pass_rows']}` guard-pass rows.",
                f"- Orders: `{orders.get('actions', {})}`.",
                f"- MT5 report: `{result['html_report']}`",
                f"- Trade ledger: `{result['trade_csv']}`",
                f"- Signal ledger: `{result['signal_csv']}`",
                "",
            ]
        )
        if result.get("error"):
            lines.insert(-1, f"- Error: `{result['error']}`.")
    lines.extend(
        [
            "## Verdict",
            "",
            f"`{payload['winner']['status']}`.",
            "",
            "Reviewer spend is reserved for a core WR/W-L hit or a serious methodological fork. This report alone does not authorize runtime use.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_mt5_date(value: str) -> date:
    return datetime.strptime(value, "%Y.%m.%d").date()


def trading_weekday_count(start: date, end: date) -> int:
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def lower_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() == "true"


def format_ratio(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def money(value: float, currency: str) -> str:
    return f"{value:.2f} {currency}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MT5 Strategy Tester variants for A3 XAU round-retest RR2 probe.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="MT5 date, e.g. 2022.07.01")
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE, help="MT5 date, e.g. 2026.06.30")
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Report tag.")
    parser.add_argument("--backtest-root", type=Path, default=DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=DEFAULT_METAEDITOR)
    parser.add_argument(
        "--variant",
        action="append",
        choices=[variant.name for variant in VARIANTS],
        help="Run only selected variant(s). May be passed multiple times.",
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    parser.add_argument("--deposit", default="1808.13", help="Tester deposit amount.")
    parser.add_argument("--currency", default="AED", help="Tester deposit currency.")
    args = parser.parse_args()

    safe_tag = safe_name(args.tag)
    report_md = PHASE1_ROOT / "outputs" / "reports" / f"A3_ROUND_RETEST_RR2_MT5_PROBE_{safe_tag}.md"
    report_json = report_md.with_suffix(".json")
    payload = run_variants(
        backtest_root=args.backtest_root,
        metaeditor=args.metaeditor,
        from_date=args.from_date,
        to_date=args.to_date,
        tag=args.tag,
        report_md=report_md,
        report_json=report_json,
        variant_names=set(args.variant) if args.variant else None,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit=args.deposit,
        currency=args.currency,
    )
    print(
        json.dumps(
            {
                "status": payload["winner"]["status"],
                "winner": payload["winner"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
