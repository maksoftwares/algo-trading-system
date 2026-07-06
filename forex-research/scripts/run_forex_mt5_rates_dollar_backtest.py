from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any


FOREX_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = FOREX_ROOT.parent
EA_NAME = "ForexRatesDollarYieldPressureShortSessionV1"
EA_SOURCE = FOREX_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_BACKTEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_METAEDITOR = DEFAULT_BACKTEST_ROOT / "MetaEditor64.exe"
DEFAULT_OUTPUT_DIR = FOREX_ROOT / "outputs" / "reports" / "mt5_backtests"
DEFAULT_FROM_DATE = "2022.01.01"
DEFAULT_TO_DATE = "2026.07.02"
DEFAULT_TAG = "2022_2026_RATES_DOLLAR_V1"
CONTEXT_FILE_NAME = "forex_rates_dollar_context.csv"
REFERENCE_ETF_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "etf"
RECENT_RATES_ROOT = FOREX_ROOT / "data" / "external" / "yahoo_etf" / "rates_dollar"


@dataclass(frozen=True)
class BacktestScope:
    from_date: str
    to_date: str
    tag: str
    symbol: str
    period: str
    server_utc_offset_hours: int
    deposit: str
    currency: str


def run_backtest(
    *,
    backtest_root: Path,
    metaeditor: Path,
    output_dir: Path,
    scope: BacktestScope,
    timeout_seconds: int,
) -> dict[str, Any]:
    require_file(EA_SOURCE)
    require_file(backtest_root / "terminal64.exe")
    require_file(metaeditor)
    terminal = backtest_root / "terminal64.exe"

    output_dir.mkdir(parents=True, exist_ok=True)
    context_repo_path = output_dir / CONTEXT_FILE_NAME
    context_rows, context_sources = build_context_csv(context_repo_path)
    context_hash = sha256_file(context_repo_path)
    compile_log = compile_ea(backtest_root, metaeditor)
    copy_context_to_tester_roots(backtest_root, context_repo_path)

    report_base = f"ForexRatesDollar_{scope.tag}_{scope.symbol}_{scope.period}_offset{scope.server_utc_offset_hours}"
    startup_log = f"{report_base}_startup_log.csv"
    signal_log = f"{report_base}_signal_log.csv"
    order_log = f"{report_base}_order_log.csv"
    remove_old_files(backtest_root, report_base, startup_log, signal_log, order_log)
    config = write_config(
        backtest_root=backtest_root,
        report_base=report_base,
        startup_log=startup_log,
        signal_log=signal_log,
        order_log=order_log,
        scope=scope,
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
        raise RuntimeError(f"Timed out waiting for MT5 Strategy Tester: {report_base}")

    elapsed_seconds = round((datetime.now(timezone.utc) - started).total_seconds(), 2)
    html_report = backtest_root / "Reports" / f"{report_base}.htm"
    if not html_report.exists():
        raise RuntimeError(f"MT5 did not produce report: {html_report}")

    trades, metrics = parse_mt5_report(html_report, scope.symbol)
    bars = integer_metric(metrics.get("Bars", "0"))
    ticks = integer_metric(metrics.get("Ticks", "0"))
    if bars <= 0 or ticks <= 0:
        raise RuntimeError(f"MT5 tester returned zero bars/ticks: bars={bars}, ticks={ticks}, report={html_report}")

    run_dir = output_dir / report_base
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_report = run_dir / html_report.name
    copied_config = run_dir / config.name
    copied_context = run_dir / context_repo_path.name
    copied_startup_log = run_dir / startup_log
    copied_signal_log = run_dir / signal_log
    copied_order_log = run_dir / order_log
    copied_trades_csv = run_dir / f"{report_base}_trades.csv"
    copied_summary = run_dir / f"{report_base}_summary.json"

    shutil.copy2(html_report, copied_report)
    shutil.copy2(config, copied_config)
    shutil.copy2(context_repo_path, copied_context)
    copy_tester_file(backtest_root, startup_log, copied_startup_log)
    copy_tester_file(backtest_root, signal_log, copied_signal_log)
    copy_tester_file(backtest_root, order_log, copied_order_log)
    write_trades(copied_trades_csv, trades)

    signal_rows = read_csv_rows(copied_signal_log)
    order_rows = read_csv_rows(copied_order_log)
    startup_rows = read_csv_rows(copied_startup_log)
    summary = summarize_trades(trades)
    decision = decide(summary["overall"], metrics)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "candidate_id": "eurusd_h4_rates_dollar_yield_pressure_short_session_v1",
        "status": decision["status"],
        "decision": decision,
        "scope": {
            "ea": EA_NAME,
            "symbol": scope.symbol,
            "period": scope.period,
            "from_date": scope.from_date,
            "to_date": scope.to_date,
            "tag": scope.tag,
            "terminal_sandbox": str(backtest_root),
            "tester_model": "MT5 Strategy Tester Model=0 every tick",
            "server_utc_offset_hours": scope.server_utc_offset_hours,
            "deposit": scope.deposit,
            "currency": scope.currency,
            "runtime_boundary": "Strategy Tester only; EA fails OnInit outside MQL_TESTER.",
        },
        "context": {
            "file": str(copied_context),
            "sha256": context_hash,
            "rows": context_rows,
            "sources": context_sources,
            "lag_policy": "Daily ETF observations are available from next UTC date at 00:00.",
        },
        "artifacts": {
            "compile_log": str(compile_log),
            "tester_config": str(copied_config),
            "mt5_report": str(copied_report),
            "startup_log": str(copied_startup_log),
            "signal_log": str(copied_signal_log),
            "order_log": str(copied_order_log),
            "trade_csv": str(copied_trades_csv),
            "summary_json": str(copied_summary),
        },
        "elapsed_seconds": elapsed_seconds,
        "mt5_report_metrics": metrics,
        "summary": summary,
        "activity": {
            "startup_rows": len(startup_rows),
            "signal_rows": len(signal_rows),
            "order_rows": len(order_rows),
            "order_actions": dict(Counter(row.get("action", "") for row in order_rows)),
            "order_reasons": dict(Counter(order_reason(row) for row in order_rows)),
        },
        "boundary": {
            "active_terminal_process_used": False,
            "strategy_tester_launched": True,
            "live_or_demo_chart_touched": False,
            "order_or_position_touched_outside_tester": False,
            "python_price_backtest_used_for_result": False,
        },
    }
    copied_summary.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report_md = output_dir / f"FOREX_MT5_RATES_DOLLAR_BACKTEST_{scope.tag}.md"
    report_json = report_md.with_suffix(".json")
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    payload["artifacts"]["report_md"] = str(report_md)
    payload["artifacts"]["report_json"] = str(report_json)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def build_context_csv(destination: Path) -> tuple[int, dict[str, str]]:
    tlt_uup_files = [
        REFERENCE_ETF_ROOT / "tlt_uup_daily_yahoo_2015_2025.csv",
        latest_file(RECENT_RATES_ROOT, "tlt_uup_daily_yahoo_*.csv"),
    ]
    tlt_shy_files = [
        REFERENCE_ETF_ROOT / "tlt_shy_daily_yahoo_2015_2025.csv",
        latest_file(RECENT_RATES_ROOT, "tlt_shy_daily_yahoo_*.csv"),
    ]
    for path in [*tlt_uup_files, *tlt_shy_files]:
        require_file(path)

    uup = read_ratio_by_date(tlt_uup_files, "tlt_close", "uup_close")
    shy = read_ratio_by_date(tlt_shy_files, "tlt_close", "shy_close")
    dates = sorted(set(uup).intersection(shy))
    rows: list[dict[str, Any]] = []
    for idx, obs_date in enumerate(dates):
        if idx < 20:
            continue
        tlt_uup_5d = pct_change(uup, dates, idx, 5)
        tlt_uup_20d = pct_change(uup, dates, idx, 20)
        tlt_shy_20d = pct_change(shy, dates, idx, 20)
        if tlt_uup_5d is None or tlt_uup_20d is None or tlt_shy_20d is None:
            continue
        available_date = obs_date + timedelta(days=1)
        available_epoch = int(datetime.combine(available_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
        rows.append(
            {
                "available_epoch": available_epoch,
                "tlt_uup_5d_pct": f"{tlt_uup_5d:.10f}",
                "tlt_uup_20d_pct": f"{tlt_uup_20d:.10f}",
                "tlt_shy_20d_pct": f"{tlt_shy_20d:.10f}",
                "observation_date_utc": obs_date.isoformat(),
            }
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "available_epoch",
                "tlt_uup_5d_pct",
                "tlt_uup_20d_pct",
                "tlt_shy_20d_pct",
                "observation_date_utc",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    sources = {
        "tlt_uup_reference": relative(tlt_uup_files[0]),
        "tlt_uup_recent": relative(tlt_uup_files[1]),
        "tlt_shy_reference": relative(tlt_shy_files[0]),
        "tlt_shy_recent": relative(tlt_shy_files[1]),
    }
    return len(rows), sources


def read_ratio_by_date(paths: list[Path], duration_column: str, denominator_column: str) -> dict[date, float]:
    values: dict[date, float] = {}
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                raw_date = row.get("date_utc", "")
                if not raw_date:
                    continue
                try:
                    obs_date = date.fromisoformat(raw_date[:10])
                    duration = float(row[duration_column])
                    denominator = float(row[denominator_column])
                except (KeyError, ValueError):
                    continue
                if duration > 0 and denominator > 0:
                    values[obs_date] = duration / denominator
    return values


def pct_change(values: dict[date, float], dates: list[date], idx: int, lag: int) -> float | None:
    if idx - lag < 0:
        return None
    current = values.get(dates[idx])
    previous = values.get(dates[idx - lag])
    if current is None or previous is None or previous <= 0:
        return None
    return (current / previous - 1.0) * 100.0


def latest_file(root: Path, pattern: str) -> Path:
    files = sorted(root.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files match {root / pattern}")
    return files[-1]


def compile_ea(backtest_root: Path, metaeditor: Path) -> Path:
    experts = backtest_root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target = experts / f"{EA_NAME}.mq5"
    shutil.copy2(EA_SOURCE, target)
    log = backtest_root / "Logs" / f"compile_{EA_NAME}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(metaeditor), f"/compile:{target}", f"/log:{log}"],
        cwd=str(backtest_root),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    ex5 = experts / f"{EA_NAME}.ex5"
    if not ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{read_text(log)}")
    log_text = read_text(log).lower()
    if "error(s)" in log_text and "0 error(s)" not in log_text:
        raise RuntimeError(f"MetaEditor compile reported errors:\n{read_text(log)}")
    return log


def copy_context_to_tester_roots(backtest_root: Path, source: Path) -> None:
    roots = [
        backtest_root / "MQL5" / "Files",
        backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files",
    ]
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, root / CONTEXT_FILE_NAME)


def write_config(
    *,
    backtest_root: Path,
    report_base: str,
    startup_log: str,
    signal_log: str,
    order_log: str,
    scope: BacktestScope,
) -> Path:
    inputs = {
        "InpRunId": f"MT5_{report_base}",
        "InpTargetSymbol": scope.symbol,
        "InpMagicNumber": "26070301",
        "InpFixedLots": "0.01",
        "InpDeviationPoints": "20",
        "InpMaxSpreadPoints": "0",
        "InpMinStopPoints": "5",
        "InpTargetR": "1.35",
        "InpMaxHoldH4Bars": "14",
        "InpAtrPeriod": "14",
        "InpEmaFastPeriod": "20",
        "InpEmaMidPeriod": "50",
        "InpEmaSlowPeriod": "100",
        "InpWarmupBars": "260",
        "InpServerUtcOffsetHours": str(scope.server_utc_offset_hours),
        "InpContextCsvFileName": CONTEXT_FILE_NAME,
        "InpStartupLogFileName": startup_log,
        "InpSignalLogFileName": signal_log,
        "InpOrderLogFileName": order_log,
        "InpOrderComment": "FX_RATE_DOLLAR_V1",
    }
    lines = [
        "[Common]",
        "Login=1025742",
        "Server=Capital.ComMena-Demo",
        "KeepPrivate=1",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={EA_NAME}.ex5",
        f"Symbol={scope.symbol}",
        f"Period={scope.period}",
        "Optimization=0",
        "Model=0",
        "Dates=2",
        f"FromDate={scope.from_date}",
        f"ToDate={scope.to_date}",
        "ForwardMode=0",
        f"Deposit={scope.deposit}",
        f"Currency={scope.currency}",
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


def write_trades(path: Path, trades: list[dict[str, Any]]) -> None:
    fieldnames = list(trades[0].keys()) if trades else ["exit_time"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"overall": aggregate(trades)}
    for key in ["direction", "entry_date", "entry_hour"]:
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
        "avg_pnl": round(pnl / count, 2) if count else 0.0,
    }


def decide(overall: dict[str, Any], metrics: dict[str, str]) -> dict[str, str]:
    trades = int(overall["trades"])
    pnl = float(overall["pnl"])
    pf = overall["profit_factor"]
    if trades < 20:
        status = "REJECT_MT5_LOW_SAMPLE"
    elif pnl <= 0:
        status = "REJECT_MT5_NEGATIVE_NET"
    elif pf is None or float(pf) < 1.15:
        status = "REJECT_MT5_WEAK_EDGE"
    else:
        status = "WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL"
    return {
        "status": status,
        "note": "MT5 Strategy Tester result only. A pass is watchlist-only until split, top-winner, rolling-window, and fresh-data robustness are complete.",
        "total_net_profit": metrics.get("Total Net Profit", ""),
        "profit_factor_reported": metrics.get("Profit Factor", ""),
        "total_trades_reported": metrics.get("Total Trades", ""),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    overall = payload["summary"]["overall"]
    metrics = payload["mt5_report_metrics"]
    artifacts = payload["artifacts"]
    currency = payload["scope"]["currency"]
    lines = [
        "# Forex MT5 Rates/Dollar Backtest",
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Candidate: `{payload['candidate_id']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Actual MT5 Strategy Tester was used for the price path, fills, spread, stops, targets, and max-hold exits.",
        "- Python was used only to prepare the fixed lagged ETF context file and parse the finished MT5 report.",
        "- The EA fails initialization outside `MQL_TESTER`; no live/demo chart, order, or position was touched.",
        f"- Isolated tester root: `{payload['scope']['terminal_sandbox']}`.",
        "",
        "## Scope",
        "",
        f"- Symbol/period: `{payload['scope']['symbol']} {payload['scope']['period']}`.",
        f"- Window: `{payload['scope']['from_date']} -> {payload['scope']['to_date']}`.",
        f"- Server UTC offset input: `{payload['scope']['server_utc_offset_hours']}` hours.",
        f"- Context rows/SHA256: `{payload['context']['rows']}` / `{payload['context']['sha256']}`.",
        "",
        "## Result",
        "",
        f"| Trades | Win Rate | Net {currency} | PF | Gross Profit | Gross Loss | MT5 PF | MT5 Total Trades | Equity DD Max |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| `{overall['trades']}` | `{overall['win_rate_pct']}%` | `{overall['pnl']}` | "
            f"`{overall['profit_factor']}` | `{overall['gross_profit']}` | `{overall['gross_loss']}` | "
            f"`{metrics.get('Profit Factor', '')}` | `{metrics.get('Total Trades', '')}` | "
            f"`{metrics.get('Equity Drawdown Maximal', '')}` |"
        ),
        "",
        "## Activity",
        "",
        f"- Signals logged by EA: `{payload['activity']['signal_rows']}`.",
        f"- Order log rows: `{payload['activity']['order_rows']}`.",
        f"- Order actions: `{json.dumps(payload['activity']['order_actions'], sort_keys=True)}`.",
        f"- Order reasons: `{json.dumps(payload['activity']['order_reasons'], sort_keys=True)}`.",
        "",
        "## Artifacts",
        "",
        f"- MT5 report: `{artifacts['mt5_report']}`",
        f"- Tester config: `{artifacts['tester_config']}`",
        f"- Summary JSON: `{artifacts['summary_json']}`",
        f"- Trades CSV: `{artifacts['trade_csv']}`",
        f"- Signal log: `{artifacts['signal_log']}`",
        f"- Order log: `{artifacts['order_log']}`",
        "",
        "## Interpretation",
        "",
        payload["decision"]["note"],
        "",
    ]
    return "\n".join(lines)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def order_reason(row: dict[str, str]) -> str:
    combined = row.get("deal_and_reason", "")
    match = re.search(r"\|reason=([^|]+)", combined)
    return match.group(1) if match else combined or row.get("retcode_description", "")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip().upper())
    return cleaned.strip("_") or "MT5_FOREX"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the EURUSD H4 rates/dollar clue in MT5 Strategy Tester.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="MT5 date, e.g. 2022.01.01")
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE, help="MT5 date, e.g. 2026.07.02")
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--period", default="H4")
    parser.add_argument("--server-utc-offset-hours", type=int, default=0)
    parser.add_argument("--backtest-root", type=Path, default=DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=DEFAULT_METAEDITOR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()
    scope = BacktestScope(
        from_date=args.from_date,
        to_date=args.to_date,
        tag=safe_name(args.tag),
        symbol=args.symbol,
        period=args.period,
        server_utc_offset_hours=args.server_utc_offset_hours,
        deposit=args.deposit,
        currency=args.currency,
    )
    payload = run_backtest(
        backtest_root=args.backtest_root,
        metaeditor=args.metaeditor,
        output_dir=args.output_dir,
        scope=scope,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "summary": payload["summary"]["overall"],
                "mt5_profit_factor": payload["mt5_report_metrics"].get("Profit Factor", ""),
                "report_md": payload["artifacts"].get("report_md", ""),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
