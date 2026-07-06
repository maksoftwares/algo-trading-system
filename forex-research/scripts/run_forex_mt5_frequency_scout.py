from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FOREX_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = FOREX_ROOT.parent
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
EA_NAME = "A1XauM5MomentumContinuationExecutor"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_BACKTEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_METAEDITOR = DEFAULT_BACKTEST_ROOT / "MetaEditor64.exe"
DEFAULT_OUTPUT_DIR = FOREX_ROOT / "outputs" / "reports" / "mt5_backtests" / "frequency_scout"
DEFAULT_FROM_DATE = "2024.07.01"
DEFAULT_TO_DATE = "2026.07.02"
DEFAULT_TAG = "CURRENT_2024_2026_M5_FREQ_FIRST"
DEFAULT_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")


@dataclass(frozen=True)
class Variant:
    name: str
    signal_mode: str
    description: str
    inputs: dict[str, str]


VARIANTS = [
    Variant(
        name="m5_ema_trend",
        signal_mode="5",
        description="M5 EMA trend continuation, no HTF filter.",
        inputs={
            "InpSignalMode": "5",
            "InpM5TrendEmaFastPeriod": "8",
            "InpM5TrendEmaSlowPeriod": "21",
            "InpM5TrendSlopeBars": "3",
            "InpM5TrendMinSlopeAtr": "0.05",
            "InpM5TrendMaxDistanceAtr": "1.20",
        },
    ),
    Variant(
        name="ema_pullback",
        signal_mode="1",
        description="M5 EMA20 pullback continuation, no HTF filter.",
        inputs={
            "InpSignalMode": "1",
            "InpPullbackEmaPeriod": "20",
            "InpPullbackTouchAtr": "0.25",
        },
    ),
    Variant(
        name="break_and_run",
        signal_mode="0",
        description="M5 local range break-and-run continuation, no HTF filter.",
        inputs={
            "InpSignalMode": "0",
            "InpBreakLookbackBars": "12",
            "InpBreakAtrMultiple": "0.20",
        },
    ),
    Variant(
        name="sweep_reclaim",
        signal_mode="3",
        description="M5 sweep/reclaim reversal, no HTF filter.",
        inputs={
            "InpSignalMode": "3",
            "InpSweepLookbackBars": "12",
            "InpSweepAtrMultiple": "0.10",
            "InpReclaimAtrMultiple": "0.05",
        },
    ),
    Variant(
        name="compression_expansion",
        signal_mode="2",
        description="M5 compression then range expansion, no HTF filter.",
        inputs={
            "InpSignalMode": "2",
            "InpCompressionLookbackBars": "8",
            "InpCompressionMaxRangeAtr": "1.20",
            "InpCompressionBreakAtrMultiple": "0.10",
        },
    ),
    Variant(
        name="opening_range",
        signal_mode="4",
        description="M5 opening-range continuation, no HTF filter.",
        inputs={
            "InpSignalMode": "4",
            "InpOpeningRangeStartHour": "7",
            "InpOpeningRangeMinutes": "60",
            "InpOpeningTradeWindowHours": "5",
            "InpOpeningBreakAtrMultiple": "0.10",
        },
    ),
]


COMMON_INPUTS = {
    "InpAllowDemoTrading": "true",
    "InpAllowNonDemoAccounts": "false",
    "InpAllowedAccountLogin": "1025742",
    "InpExpectedServerMarker": "Demo",
    "InpFixedLots": "0.01",
    "InpUseRiskNormalizedLots": "false",
    "InpDeviationPoints": "30",
    "InpMaxSpreadPoints": "100",
    "InpMaxEstimatedCostR": "999.0",
    "InpMaxTradesPerDay": "20",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "true",
    "InpDirectionMode": "0",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpUseDirectionalSessionFilter": "false",
    "InpMinRangeAtr": "0.50",
    "InpMinBodyFraction": "0.40",
    "InpLongCloseLocation": "0.68",
    "InpShortCloseLocation": "0.32",
    "InpMinThreeBarMoveAtr": "0.50",
    "InpMaxThreeBarMoveAtr": "0.00",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpStopAtrMultiple": "1.40",
    "InpStopFloorPoints": "30",
    "InpStopCeilingPoints": "700",
    "InpRiskReward": "1.00",
    "InpBlockedEntryHoursCsv": "",
    "InpPortfolioDailyGuardEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpSignalClaimEnabled": "false",
}


def run_scout(
    *,
    backtest_root: Path,
    metaeditor: Path,
    ea_name: str,
    ea_source: Path,
    output_dir: Path,
    from_date: str,
    to_date: str,
    tag: str,
    symbols: list[str],
    variants: list[Variant],
    timeout_seconds: int,
    deposit: str,
    currency: str,
    tuning_attempted: bool = False,
) -> dict[str, Any]:
    require_file(ea_source)
    require_file(backtest_root / "terminal64.exe")
    require_file(metaeditor)
    output_dir.mkdir(parents=True, exist_ok=True)
    compile_log = compile_ea(backtest_root, metaeditor, ea_name, ea_source)
    results = []
    for symbol in symbols:
        for index, variant in enumerate(variants):
            result = run_variant(
                backtest_root=backtest_root,
                terminal=backtest_root / "terminal64.exe",
                output_dir=output_dir,
                ea_name=ea_name,
                symbol=symbol,
                variant=variant,
                variant_index=index,
                from_date=from_date,
                to_date=to_date,
                tag=tag,
                timeout_seconds=timeout_seconds,
                deposit=deposit,
                currency=currency,
            )
            results.append(result)

    ranked = sorted(
        results,
        key=lambda item: (
            item["summary"]["overall"]["trades"],
            item["summary"]["overall"]["profit_factor"] or 0.0,
            item["summary"]["overall"]["pnl"],
        ),
        reverse=True,
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "MT5_FREQUENCY_SCOUT_COMPLETE_RESEARCH_ONLY",
        "scope": {
            "ea": ea_name,
            "source_ea": str(ea_source),
            "from_date": from_date,
            "to_date": to_date,
            "tag": tag,
            "symbols": symbols,
            "period": "M5",
            "terminal_sandbox": str(backtest_root),
            "tester_model": "MT5 Strategy Tester Model=0 every tick",
            "frequency_first": True,
            "tuning_attempted": tuning_attempted,
            "currency": currency,
        },
        "compile_log": str(compile_log),
        "results": ranked,
        "boundary": {
            "active_terminal_process_used": False,
            "strategy_tester_launched": True,
            "live_or_demo_chart_touched": False,
            "order_or_position_touched_outside_tester": False,
            "python_price_backtest_used_for_result": False,
        },
        "next_step": choose_next_step(ranked),
    }
    report_md = output_dir / f"FOREX_MT5_FREQUENCY_SCOUT_{tag}.md"
    report_json = report_md.with_suffix(".json")
    payload["artifacts"] = {"report_md": str(report_md), "report_json": str(report_json)}
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def compile_ea(backtest_root: Path, metaeditor: Path, ea_name: str, ea_source: Path) -> Path:
    experts = backtest_root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target = experts / f"{ea_name}.mq5"
    shutil.copy2(ea_source, target)
    log = backtest_root / "Logs" / f"compile_{ea_name}_forex_freq_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(metaeditor), f"/compile:{target}", f"/log:{log}"],
        cwd=str(backtest_root),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    ex5 = experts / f"{ea_name}.ex5"
    if not ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{read_text(log)}")
    log_text = read_text(log).lower()
    if "error(s)" in log_text and "0 error(s)" not in log_text:
        raise RuntimeError(f"MetaEditor compile reported errors:\n{read_text(log)}")
    return log


def run_variant(
    *,
    backtest_root: Path,
    terminal: Path,
    output_dir: Path,
    ea_name: str,
    symbol: str,
    variant: Variant,
    variant_index: int,
    from_date: str,
    to_date: str,
    tag: str,
    timeout_seconds: int,
    deposit: str,
    currency: str,
) -> dict[str, Any]:
    report_base = f"ForexFreqScout_{tag}_{symbol}_M5_{variant.name}"
    startup_log = f"{report_base}_startup_log.csv"
    signal_log = f"{report_base}_signal_log.csv"
    order_log = f"{report_base}_order_log.csv"
    management_log = f"{report_base}_management_log.csv"
    remove_old_files(backtest_root, report_base, startup_log, signal_log, order_log, management_log)
    config = write_config(
        backtest_root=backtest_root,
        ea_name=ea_name,
        report_base=report_base,
        startup_log=startup_log,
        signal_log=signal_log,
        order_log=order_log,
        management_log=management_log,
        symbol=symbol,
        variant=variant,
        variant_index=variant_index,
        from_date=from_date,
        to_date=to_date,
        tag=tag,
        deposit=deposit,
        currency=currency,
    )

    started = datetime.now(timezone.utc)
    process = subprocess.Popen(
        [str(terminal), "/portable", f"/config:{config}"],
        cwd=str(backtest_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError(f"Timed out waiting for MT5 tester variant {symbol} {variant.name}.")

    elapsed_seconds = round((datetime.now(timezone.utc) - started).total_seconds(), 2)
    html_report = backtest_root / "Reports" / f"{report_base}.htm"
    if not html_report.exists():
        raise RuntimeError(f"Missing MT5 report for {symbol} {variant.name}: {html_report}")
    trades, metrics = parse_mt5_report(html_report, symbol)
    bars = integer_metric(metrics.get("Bars", "0"))
    ticks = integer_metric(metrics.get("Ticks", "0"))
    if bars <= 0 or ticks <= 0:
        raise RuntimeError(f"MT5 returned zero bars/ticks for {symbol} {variant.name}: bars={bars}, ticks={ticks}")

    run_dir = output_dir / report_base
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_report = run_dir / html_report.name
    copied_config = run_dir / config.name
    copied_trades = run_dir / f"{report_base}_trades.csv"
    copied_startup = run_dir / startup_log
    copied_signal = run_dir / signal_log
    copied_order = run_dir / order_log
    copied_management = run_dir / management_log
    copied_summary = run_dir / f"{report_base}_summary.json"
    shutil.copy2(html_report, copied_report)
    shutil.copy2(config, copied_config)
    copy_tester_file(backtest_root, startup_log, copied_startup)
    copy_tester_file(backtest_root, signal_log, copied_signal)
    copy_tester_file(backtest_root, order_log, copied_order)
    copy_tester_file(backtest_root, management_log, copied_management)
    write_trades(copied_trades, trades)
    summary = summarize_trades(trades)
    signal_rows = count_csv_rows(copied_signal)
    order_rows = read_csv_rows(copied_order)
    result = {
        "symbol": symbol,
        "variant": variant.name,
        "description": variant.description,
        "elapsed_seconds": elapsed_seconds,
        "status": decide_frequency_status(summary["overall"]),
        "summary": summary,
        "mt5_report_metrics": metrics,
        "activity": {
            "signal_rows": signal_rows,
            "order_rows": len(order_rows),
            "order_actions": dict(defaultdict(int, counter_pairs(row.get("action", "") for row in order_rows))),
            "guard_reasons_top": top_counter(order_reason(row) for row in order_rows),
        },
        "artifacts": {
            "mt5_report": str(copied_report),
            "tester_config": str(copied_config),
            "trade_csv": str(copied_trades),
            "startup_log": str(copied_startup),
            "signal_log": str(copied_signal),
            "order_log": str(copied_order),
            "management_log": str(copied_management),
            "summary_json": str(copied_summary),
        },
    }
    copied_summary.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def write_config(
    *,
    backtest_root: Path,
    ea_name: str,
    report_base: str,
    startup_log: str,
    signal_log: str,
    order_log: str,
    management_log: str,
    symbol: str,
    variant: Variant,
    variant_index: int,
    from_date: str,
    to_date: str,
    tag: str,
    deposit: str,
    currency: str,
) -> Path:
    point_settings = symbol_point_settings(symbol)
    inputs = {
        **COMMON_INPUTS,
        **point_settings,
        **variant.inputs,
        "InpRunId": f"MT5_FREQ_{tag}_{symbol}_{variant.name}",
        "InpTargetSymbol": symbol,
        "InpMagicNumber": str(26070400 + variant_index + 100 * DEFAULT_SYMBOLS.index(symbol) if symbol in DEFAULT_SYMBOLS else 26070400 + variant_index),
        "InpStartupLogFileName": startup_log,
        "InpSignalLogFileName": signal_log,
        "InpOrderLogFileName": order_log,
        "InpManagementLogFileName": management_log,
        "InpOrderComment": f"FXFREQ_{symbol}_{variant.name[:8].upper()}",
    }
    lines = [
        "[Common]",
        "Login=1025742",
        "Server=Capital.ComMena-Demo",
        "KeepPrivate=1",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={ea_name}.ex5",
        f"Symbol={symbol}",
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


def symbol_point_settings(symbol: str) -> dict[str, str]:
    if "JPY" in symbol:
        return {
            "InpMaxSpreadPoints": "120",
            "InpStopFloorPoints": "30",
            "InpStopCeilingPoints": "900",
            "InpDeviationPoints": "40",
        }
    return {
        "InpMaxSpreadPoints": "100",
        "InpStopFloorPoints": "30",
        "InpStopCeilingPoints": "700",
        "InpDeviationPoints": "30",
    }


def remove_old_files(backtest_root: Path, report_base: str, *log_names: str) -> None:
    for suffix in [".htm", ".png", "-holding.png", "-mfemae.png", "-hst.png"]:
        path = backtest_root / "Reports" / f"{report_base}{suffix}"
        if path.exists():
            path.unlink()
    files_root = backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    for name in log_names:
        path = files_root / name
        if path.exists():
            path.unlink()


def copy_tester_file(backtest_root: Path, log_name: str, destination: Path) -> None:
    source = backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files" / log_name
    if source.exists():
        shutil.copy2(source, destination)
    else:
        destination.write_text("", encoding="utf-8")


def parse_mt5_report(path: Path, symbol: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    text = read_text(path)
    rows = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        cleaned = [html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ") for cell in cells]
        if cleaned:
            rows.append(cleaned)
    metrics = parse_metrics(rows)
    trades = []
    open_trades: list[dict[str, Any]] = []
    for cells in rows:
        if len(cells) < 13 or cells[2] != symbol or cells[4] not in {"in", "out"}:
            continue
        try:
            deal_time = datetime.strptime(cells[0], "%Y.%m.%d %H:%M:%S")
            profit = parse_float(cells[10])
            balance = parse_float(cells[11])
        except ValueError:
            continue
        deal_type = cells[3].lower()
        if cells[4] == "in":
            open_trades.append(
                {
                    "entry_time": cells[0],
                    "entry_date": deal_time.date().isoformat(),
                    "entry_hour": deal_time.hour,
                    "direction": "LONG" if deal_type == "buy" else "SHORT",
                    "entry_deal": cells[1],
                    "volume": cells[5],
                    "entry_price": cells[6],
                    "entry_comment": cells[12],
                }
            )
            continue
        exit_direction = "LONG" if deal_type == "sell" else "SHORT"
        open_index = next((i for i, trade in enumerate(open_trades) if trade["direction"] == exit_direction), None)
        if open_index is None:
            continue
        open_trade = open_trades.pop(open_index)
        trades.append(
            {
                **open_trade,
                "exit_time": cells[0],
                "exit_date": deal_time.date().isoformat(),
                "exit_hour": deal_time.hour,
                "exit_deal": cells[1],
                "exit_price": cells[6],
                "profit": profit,
                "balance": balance,
                "exit_comment": cells[12],
            }
        )
    return trades, metrics


def parse_metrics(rows: list[list[str]]) -> dict[str, str]:
    flat = [cell for row in rows for cell in row]
    labels = [
        "History Quality:",
        "Bars:",
        "Ticks:",
        "Total Net Profit:",
        "Gross Profit:",
        "Gross Loss:",
        "Profit Factor:",
        "Expected Payoff:",
        "Recovery Factor:",
        "Sharpe Ratio:",
        "Total Trades:",
        "Short Trades (won %):",
        "Long Trades (won %):",
        "Profit Trades (% of total):",
        "Loss Trades (% of total):",
        "Total Deals:",
        "Balance Drawdown Maximal:",
        "Equity Drawdown Maximal:",
        "Balance Drawdown Relative:",
        "Equity Drawdown Relative:",
    ]
    metrics = {}
    for idx, cell in enumerate(flat):
        if cell in labels and idx + 1 < len(flat):
            metrics[cell.rstrip(":")] = flat[idx + 1]
    return metrics


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"overall": aggregate(trades)}
    for key in ["direction", "entry_hour"]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade.get(key, ""))].append(trade)
        summary[key] = {name: aggregate(items) for name, items in sorted(grouped.items())}
    return summary


def aggregate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(trades)
    wins = sum(1 for trade in trades if trade["profit"] > 0)
    losses = sum(1 for trade in trades if trade["profit"] < 0)
    gross_profit = sum(trade["profit"] for trade in trades if trade["profit"] > 0)
    gross_loss = -sum(trade["profit"] for trade in trades if trade["profit"] < 0)
    pnl = gross_profit - gross_loss
    return {
        "trades": count,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round((wins / count) * 100, 2) if count else 0.0,
        "pnl": round(pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "avg_pnl": round(pnl / count, 4) if count else 0.0,
    }


def decide_frequency_status(overall: dict[str, Any]) -> str:
    trades = int(overall["trades"])
    pnl = float(overall["pnl"])
    pf = overall["profit_factor"] or 0.0
    if trades < 250:
        return "LOW_FREQUENCY_SKIP_TUNING"
    if pnl <= 0 or pf < 1.0:
        return "FREQUENT_BUT_NEGATIVE_SKIP_TUNING"
    if pf < 1.08:
        return "FREQUENT_BUT_THIN_EDGE_WATCH"
    return "FREQUENT_RAW_EDGE_TUNING_CANDIDATE"


def choose_next_step(ranked: list[dict[str, Any]]) -> dict[str, str]:
    candidates = [row for row in ranked if row["status"] == "FREQUENT_RAW_EDGE_TUNING_CANDIDATE"]
    if candidates:
        top = candidates[0]
        return {
            "status": "TUNE_TOP_FREQUENT_RAW_EDGE_NEXT",
            "symbol": top["symbol"],
            "variant": top["variant"],
            "reason": "Highest trade-count raw-edge candidate cleared the frequency-first screen.",
        }
    watches = [row for row in ranked if row["status"] == "FREQUENT_BUT_THIN_EDGE_WATCH"]
    if watches:
        top = watches[0]
        return {
            "status": "OPTIONAL_TUNE_ONLY_IF_NO_STRONGER_FAMILY",
            "symbol": top["symbol"],
            "variant": top["variant"],
            "reason": "Frequency exists but raw edge is thin; prefer another family before tuning.",
        }
    top = ranked[0] if ranked else {}
    return {
        "status": "NO_FREQUENT_RAW_EDGE_FOUND",
        "symbol": str(top.get("symbol", "")),
        "variant": str(top.get("variant", "")),
        "reason": "No row had both enough trades and positive raw edge.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    scope = payload["scope"]
    lines = [
        "# Forex MT5 Frequency-First Scout",
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Actual MT5 Strategy Tester was used for each row.",
        f"- Tuning attempted in this run: `{str(scope.get('tuning_attempted', False)).lower()}`.",
        "- No survivor/demo spec is created by this runner.",
        "- Python only compiled/launched MT5 and parsed completed MT5 reports.",
        "- No live/demo chart, preset, order, or position was touched outside Strategy Tester.",
        f"- Isolated tester root: `{scope['terminal_sandbox']}`.",
        "",
        "## Scope",
        "",
        f"- Window: `{scope['from_date']} -> {scope['to_date']}`.",
        f"- Symbols: `{', '.join(scope['symbols'])}`.",
        f"- Period: `{scope['period']}`.",
        f"- Tester model: `{scope['tester_model']}`.",
        f"- Tuning attempted: `{str(scope.get('tuning_attempted', False)).lower()}`.",
        "",
        "## Frequency Ranking",
        "",
        f"| Rank | Symbol | Variant | Status | Trades | Win Rate | Net {scope['currency']} | PF | MT5 Trades | MT5 PF | Equity DD Max |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, result in enumerate(payload["results"], start=1):
        overall = result["summary"]["overall"]
        metrics = result["mt5_report_metrics"]
        lines.append(
            f"| `{rank}` | `{result['symbol']}` | `{result['variant']}` | `{result['status']}` | "
            f"`{overall['trades']}` | `{overall['win_rate_pct']}%` | `{overall['pnl']}` | "
            f"`{overall['profit_factor']}` | `{metrics.get('Total Trades', '')}` | "
            f"`{metrics.get('Profit Factor', '')}` | `{metrics.get('Equity Drawdown Maximal', '')}` |"
        )
    next_step = payload["next_step"]
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            f"- Status: `{next_step['status']}`",
            f"- Candidate: `{next_step.get('symbol', '')} {next_step.get('variant', '')}`",
            f"- Reason: {next_step['reason']}",
            "",
            "## Artifacts",
            "",
        ]
    )
    for result in payload["results"]:
        lines.append(
            f"- `{result['symbol']} {result['variant']}`: report `{result['artifacts']['mt5_report']}`, summary `{result['artifacts']['summary_json']}`"
        )
    lines.append("")
    return "\n".join(lines)


def write_trades(path: Path, trades: list[dict[str, Any]]) -> None:
    fieldnames = list(trades[0].keys()) if trades else ["exit_time"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.readline()
        if not sample:
            return []
        delimiter = "\t" if "\t" in sample else ","
        handle.seek(0)
        return list(csv.DictReader(handle, delimiter=delimiter))


def count_csv_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def order_reason(row: dict[str, str]) -> str:
    return row.get("reason", "") or row.get("retcode_description", "")


def top_counter(values: Any, limit: int = 8) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[str(value)] += 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit])


def counter_pairs(values: Any) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[str(value)] += 1
    return counts


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_float(value: str) -> float:
    cleaned = value.replace(" ", "").replace(",", "")
    if cleaned in {"", "-"}:
        return 0.0
    return float(cleaned)


def integer_metric(value: str) -> int:
    return int(re.sub(r"[^0-9]", "", value or "0") or "0")


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip().upper())
    return cleaned.strip("_") or "MT5_FREQ"


def selected_variants(names: str) -> list[Variant]:
    if not names:
        return VARIANTS
    requested = {name.strip() for name in names.split(",") if name.strip()}
    found = [variant for variant in VARIANTS if variant.name in requested]
    missing = requested.difference({variant.name for variant in found})
    if missing:
        raise ValueError(f"Unknown variants: {', '.join(sorted(missing))}")
    return found


def expand_direction_modes(variants: list[Variant], modes_csv: str) -> list[Variant]:
    requested = [item.strip().lower() for item in modes_csv.split(",") if item.strip()]
    if not requested:
        requested = ["both"]
    mode_map = {
        "both": ("both", "0"),
        "long": ("long", "1"),
        "short": ("short", "2"),
    }
    unknown = set(requested).difference(mode_map)
    if unknown:
        raise ValueError(f"Unknown direction modes: {', '.join(sorted(unknown))}")
    if requested == ["both"]:
        return variants
    expanded: list[Variant] = []
    for variant in variants:
        for mode in requested:
            label, value = mode_map[mode]
            expanded.append(
                Variant(
                    name=f"{variant.name}_{label}",
                    signal_mode=variant.signal_mode,
                    description=f"{variant.description} Direction={label}.",
                    inputs={**variant.inputs, "InpDirectionMode": value},
                )
            )
    return expanded


def expand_session_modes(variants: list[Variant], modes_csv: str) -> list[Variant]:
    requested = [item.strip().lower() for item in modes_csv.split(",") if item.strip()]
    if not requested:
        requested = ["all"]
    mode_map = {
        "all": ("all", ""),
        "asia": ("asia", "6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23"),
        "london": ("london", "0,1,2,3,4,5,12,13,14,15,16,17,18,19,20,21,22,23"),
        "ny_morning": ("ny_morning", "0,1,2,3,4,5,6,7,8,9,10,11,17,18,19,20,21,22,23"),
        "ny_late_rollover": ("ny_late_rollover", "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16"),
    }
    unknown = set(requested).difference(mode_map)
    if unknown:
        raise ValueError(f"Unknown session modes: {', '.join(sorted(unknown))}")
    if requested == ["all"]:
        return variants
    expanded: list[Variant] = []
    for variant in variants:
        for mode in requested:
            label, blocked_hours = mode_map[mode]
            expanded.append(
                Variant(
                    name=f"{variant.name}_{label}",
                    signal_mode=variant.signal_mode,
                    description=f"{variant.description} Server-session={label}.",
                    inputs={**variant.inputs, "InpBlockedEntryHoursCsv": blocked_hours},
                )
            )
    return expanded


def expand_blocked_hour_sets(variants: list[Variant], sets_text: str) -> list[Variant]:
    requested = [item.strip() for item in sets_text.split(";") if item.strip()]
    if not requested:
        return variants

    expanded: list[Variant] = []
    for variant in variants:
        for item in requested:
            lowered = item.lower()
            if lowered in {"none", "all", "all_hours"}:
                label = "all_hours"
                blocked_hours = ""
            else:
                hours = []
                for token in re.split(r"[^0-9]+", item):
                    if not token:
                        continue
                    hour = int(token)
                    if hour < 0 or hour > 23:
                        raise ValueError(f"Blocked entry hour must be 0-23: {hour}")
                    if hour not in hours:
                        hours.append(hour)
                if not hours:
                    raise ValueError(f"Blocked hour set has no valid hours: {item}")
                label = "blockh" + "_".join(str(hour) for hour in hours)
                blocked_hours = ",".join(str(hour) for hour in hours)
            expanded.append(
                Variant(
                    name=f"{variant.name}_{label}",
                    signal_mode=variant.signal_mode,
                    description=f"{variant.description} BlockedEntryHours={blocked_hours or 'none'}.",
                    inputs={**variant.inputs, "InpBlockedEntryHoursCsv": blocked_hours},
                )
            )
    return expanded


def expand_risk_rewards(variants: list[Variant], values_csv: str) -> list[Variant]:
    requested = [item.strip() for item in values_csv.split(",") if item.strip()]
    if not requested:
        requested = ["1.00"]
    if requested == ["1.00"]:
        return variants
    expanded: list[Variant] = []
    for variant in variants:
        for value in requested:
            parsed = float(value)
            if parsed <= 0:
                raise ValueError(f"Risk/reward must be positive: {value}")
            label = f"rr{str(value).replace('.', 'p')}"
            expanded.append(
                Variant(
                    name=f"{variant.name}_{label}",
                    signal_mode=variant.signal_mode,
                    description=f"{variant.description} RiskReward={value}.",
                    inputs={**variant.inputs, "InpRiskReward": value},
                )
            )
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an MT5 frequency-first Forex M5 scout.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--variants", default="")
    parser.add_argument("--direction-modes", default="both", help="Comma-separated both,long,short. Defaults to both.")
    parser.add_argument(
        "--session-modes",
        default="all",
        help="Comma-separated all,asia,london,ny_morning,ny_late_rollover using broker server hours.",
    )
    parser.add_argument(
        "--blocked-hour-sets",
        default="",
        help="Semicolon-separated custom blocked entry-hour sets, e.g. \"1,7,21\" or \"none;1,7,21\".",
    )
    parser.add_argument("--risk-rewards", default="1.00", help="Comma-separated fixed RR values. Defaults to 1.00.")
    parser.add_argument("--backtest-root", type=Path, default=DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=DEFAULT_METAEDITOR)
    parser.add_argument("--ea-name", default=EA_NAME)
    parser.add_argument("--ea-source", type=Path, default=EA_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    variants = expand_risk_rewards(
        expand_blocked_hour_sets(
            expand_session_modes(
                expand_direction_modes(selected_variants(args.variants), args.direction_modes),
                args.session_modes,
            ),
            args.blocked_hour_sets,
        ),
        args.risk_rewards,
    )
    payload = run_scout(
        backtest_root=args.backtest_root,
        metaeditor=args.metaeditor,
        ea_name=args.ea_name,
        ea_source=args.ea_source,
        output_dir=args.output_dir,
        from_date=args.from_date,
        to_date=args.to_date,
        tag=safe_name(args.tag),
        symbols=symbols,
        variants=variants,
        timeout_seconds=args.timeout_seconds,
        deposit=args.deposit,
        currency=args.currency,
        tuning_attempted=(
            bool(args.blocked_hour_sets)
            or args.session_modes.strip().lower() != "all"
            or args.direction_modes.strip().lower() != "both"
            or args.risk_rewards.strip() != "1.00"
        ),
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "top": [
                    {
                        "symbol": row["symbol"],
                        "variant": row["variant"],
                        "status": row["status"],
                        "summary": row["summary"]["overall"],
                        "mt5_pf": row["mt5_report_metrics"].get("Profit Factor", ""),
                    }
                    for row in payload["results"][:5]
                ],
                "next_step": payload["next_step"],
                "report_md": payload["artifacts"]["report_md"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
