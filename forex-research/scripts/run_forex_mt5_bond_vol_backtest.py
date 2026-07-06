from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from run_forex_mt5_rates_dollar_backtest import (
    aggregate,
    copy_tester_file,
    integer_metric,
    order_reason,
    parse_mt5_report,
    read_csv_rows,
    read_text,
    remove_old_files,
    require_file,
    safe_name,
    sha256_file,
    summarize_trades,
    write_trades,
)


FOREX_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = FOREX_ROOT.parent
EA_NAME = "ForexBondVolAsiaCarryReliefV1"
EA_SOURCE = FOREX_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_BACKTEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_METAEDITOR = DEFAULT_BACKTEST_ROOT / "MetaEditor64.exe"
DEFAULT_OUTPUT_DIR = FOREX_ROOT / "outputs" / "reports" / "mt5_backtests" / "bond_vol_scout"
DEFAULT_FROM_DATE = "2018.01.01"
DEFAULT_TO_DATE = "2026.06.27"
DEFAULT_TAG = "FULL_2018_2026_BOND_VOL_V1_MT5"
CONTEXT_FILE_NAME = "forex_bond_vol_context.csv"
REFERENCE_MOVE_FILE = REPO_ROOT / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "rates" / "move_daily_yahoo_2015_2025.csv"
RECENT_MOVE_ROOT = FOREX_ROOT / "data" / "external" / "yahoo_rates" / "bond_vol"


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
    context_rows, context_sources, context_window = build_context_csv(context_repo_path)
    context_hash = sha256_file(context_repo_path)
    compile_log = compile_ea(backtest_root, metaeditor)
    copy_context_to_tester_roots(backtest_root, context_repo_path)

    report_base = f"ForexBondVol_{scope.tag}_{scope.symbol}_{scope.period}_offset{scope.server_utc_offset_hours}"
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
    add_year_summary(summary, trades)
    decision = decide(summary["overall"], metrics)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "candidate_id": "usdjpy_h4_bond_vol_asia_session_carry_relief_v1",
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
            "frozen_rule_note": "No parameter tuning in this runner; inputs mirror the frozen v1 EA defaults.",
        },
        "context": {
            "file": str(copied_context),
            "sha256": context_hash,
            "rows": context_rows,
            "sources": context_sources,
            "window": context_window,
            "lag_policy": "MOVE daily observations are available from next UTC date at 00:00.",
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

    report_md = output_dir / f"FOREX_MT5_BOND_VOL_BACKTEST_{scope.tag}.md"
    report_json = report_md.with_suffix(".json")
    payload["artifacts"]["report_md"] = str(report_md)
    payload["artifacts"]["report_json"] = str(report_json)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    copied_summary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_context_csv(destination: Path) -> tuple[int, dict[str, str], dict[str, str]]:
    recent_move_file = latest_file(RECENT_MOVE_ROOT, "move_daily_yahoo_*.csv")
    for path in [REFERENCE_MOVE_FILE, recent_move_file]:
        require_file(path)

    move_by_date = read_move_by_date([REFERENCE_MOVE_FILE, recent_move_file])
    dates = sorted(move_by_date)
    rows: list[dict[str, str]] = []
    for idx, obs_date in enumerate(dates):
        if idx < 20:
            continue
        move_5d = pct_change(move_by_date, dates, idx, 5)
        move_20d = pct_change(move_by_date, dates, idx, 20)
        move_z60 = zscore(move_by_date, dates, idx, 60, 40)
        if move_5d is None or move_20d is None or move_z60 is None:
            continue
        available_date = obs_date + timedelta(days=1)
        available_epoch = int(datetime.combine(available_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
        rows.append(
            {
                "available_epoch": str(available_epoch),
                "move_5d_pct": f"{move_5d:.10f}",
                "move_20d_pct": f"{move_20d:.10f}",
                "move_z60": f"{move_z60:.10f}",
                "observation_date_utc": obs_date.isoformat(),
            }
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["available_epoch", "move_5d_pct", "move_20d_pct", "move_z60", "observation_date_utc"],
        )
        writer.writeheader()
        writer.writerows(rows)

    sources = {
        "move_reference": relative(REFERENCE_MOVE_FILE),
        "move_recent": relative(recent_move_file),
        "move_reference_sha256": sha256_file(REFERENCE_MOVE_FILE),
        "move_recent_sha256": sha256_file(recent_move_file),
    }
    window = {
        "observation_start_utc": rows[0]["observation_date_utc"] if rows else "",
        "observation_end_utc": rows[-1]["observation_date_utc"] if rows else "",
        "available_through_utc": (
            datetime.fromtimestamp(int(rows[-1]["available_epoch"]), tz=timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
            if rows
            else ""
        ),
    }
    return len(rows), sources, window


def read_move_by_date(paths: list[Path]) -> dict[date, float]:
    values: dict[date, float] = {}
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                raw_date = row.get("date_utc", "")
                if not raw_date:
                    continue
                try:
                    obs_date = date.fromisoformat(raw_date[:10])
                    close = float(row["move_close"])
                except (KeyError, ValueError):
                    continue
                if close > 0:
                    values[obs_date] = close
    return values


def pct_change(values: dict[date, float], dates: list[date], idx: int, lag: int) -> float | None:
    if idx - lag < 0:
        return None
    current = values.get(dates[idx])
    previous = values.get(dates[idx - lag])
    if current is None or previous is None or previous <= 0:
        return None
    return (current / previous - 1.0) * 100.0


def zscore(values: dict[date, float], dates: list[date], idx: int, window: int, min_periods: int) -> float | None:
    start = max(0, idx - window + 1)
    sample = [values[obs_date] for obs_date in dates[start : idx + 1] if obs_date in values]
    if len(sample) < min_periods:
        return None
    std = statistics.stdev(sample)
    if std <= 0:
        return None
    return (values[dates[idx]] - statistics.mean(sample)) / std


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
        "InpMagicNumber": "26070302",
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
        "InpOrderComment": "FX_BOND_VOL_V1",
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


def add_year_summary(summary: dict[str, Any], trades: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(trade.get("entry_date", ""))[:4]].append(trade)
    summary["entry_year"] = {year: aggregate(items) for year, items in sorted(grouped.items()) if year}


def decide(overall: dict[str, Any], metrics: dict[str, str]) -> dict[str, str]:
    trades = int(overall["trades"])
    pnl = float(overall["pnl"])
    pf = overall["profit_factor"]
    if trades < 50:
        status = "REJECT_MT5_LOW_SAMPLE"
    elif pnl <= 0:
        status = "REJECT_MT5_NEGATIVE_NET"
    elif pf is None or float(pf) < 1.15:
        status = "REJECT_MT5_WEAK_EDGE"
    else:
        status = "WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL"
    return {
        "status": status,
        "note": (
            "MT5 Strategy Tester result only. A pass is watchlist-only until split, top-winner, "
            "rolling-window, fresh broker-data, and frequency adequacy checks are complete."
        ),
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
        "# Forex MT5 Bond-Vol Backtest",
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Candidate: `{payload['candidate_id']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Actual MT5 Strategy Tester was used for the price path, fills, spread, stops, targets, and max-hold exits.",
        "- Python was used only to prepare the fixed lagged MOVE context file, launch MT5, and parse the finished MT5 report.",
        "- The EA fails initialization outside `MQL_TESTER`; no live/demo chart, order, or position was touched.",
        f"- Isolated tester root: `{payload['scope']['terminal_sandbox']}`.",
        "",
        "## Scope",
        "",
        f"- Symbol/period: `{payload['scope']['symbol']} {payload['scope']['period']}`.",
        f"- Window: `{payload['scope']['from_date']} -> {payload['scope']['to_date']}`.",
        f"- Server UTC offset input: `{payload['scope']['server_utc_offset_hours']}` hours.",
        f"- Context rows/SHA256: `{payload['context']['rows']}` / `{payload['context']['sha256']}`.",
        f"- Context available through: `{payload['context']['window']['available_through_utc']}`.",
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
        "## Year Splits",
        "",
        "| Year | Trades | Net | PF | Win Rate |",
        "|---:|---:|---:|---:|---:|",
    ]
    for year, row in payload["summary"].get("entry_year", {}).items():
        lines.append(f"| `{year}` | `{row['trades']}` | `{row['pnl']}` | `{row['profit_factor']}` | `{row['win_rate_pct']}%` |")
    lines.extend(
        [
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
    )
    return "\n".join(lines)


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the USDJPY H4 bond-vol clue in MT5 Strategy Tester.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="MT5 date, e.g. 2018.01.01")
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE, help="MT5 date, e.g. 2026.06.27")
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--symbol", default="USDJPY")
    parser.add_argument("--period", default="H4")
    parser.add_argument("--server-utc-offset-hours", type=int, default=0)
    parser.add_argument("--backtest-root", type=Path, default=DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=DEFAULT_METAEDITOR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
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
