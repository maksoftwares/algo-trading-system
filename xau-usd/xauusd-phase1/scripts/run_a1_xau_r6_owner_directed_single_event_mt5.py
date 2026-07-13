"""Execute the one locked R6 event in the isolated MT5 Strategy Tester.

This validates the realized path for the only structural event found by the
owner-directed decade bar screen.  It does not convert the one-event sample into
a qualified specialist and it does not authorize demo/live broker action.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_NAME = "A1XauR6OwnerDirectedSingleEventBacktest"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_OUTPUT = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_R6_OWNER_DIRECTED_10Y_MT5_20260713"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-16", errors="ignore") if path.read_bytes()[:2] in {b"\xff\xfe", b"\xfe\xff"} else path.read_text(encoding="utf-8", errors="ignore")


def html_rows(path: Path) -> list[list[str]]:
    text = read_text(path)
    rows: list[list[str]] = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        cleaned = [html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ") for cell in cells]
        if cleaned:
            rows.append(cleaned)
    return rows


def report_metrics(rows: list[list[str]]) -> dict[str, str]:
    flat = [cell for row in rows for cell in row]
    labels = [
        "History Quality:", "Bars:", "Ticks:", "Total Net Profit:", "Gross Profit:",
        "Gross Loss:", "Profit Factor:", "Expected Payoff:", "Total Trades:",
        "Profit Trades (% of total):", "Loss Trades (% of total):", "Total Deals:",
        "Balance Drawdown Maximal:", "Equity Drawdown Maximal:",
        "Balance Drawdown Relative:", "Equity Drawdown Relative:",
    ]
    result: dict[str, str] = {}
    for index, cell in enumerate(flat):
        if cell in labels and index + 1 < len(flat):
            result[cell.rstrip(":")] = flat[index + 1]
    return result


def deal_rows(rows: list[list[str]]) -> list[dict[str, str]]:
    deals: list[dict[str, str]] = []
    for cells in rows:
        if len(cells) < 13 or cells[2] != "XAUUSD" or cells[4] not in {"in", "out"}:
            continue
        deals.append(
            {
                "time": cells[0], "deal": cells[1], "symbol": cells[2], "type": cells[3],
                "direction": cells[4], "volume": cells[5], "price": cells[6],
                "commission": cells[7], "swap": cells[8], "profit": cells[10],
                "balance": cells[11], "comment": cells[12],
            }
        )
    return deals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tester-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--from-date", default="2016.07.01")
    parser.add_argument("--to-date", default="2026.07.01")
    parser.add_argument("--report-base", default="A1_XAU_R6_OWNER_DIRECTED_10Y_MT5_20260713")
    args = parser.parse_args()
    root = args.tester_root.resolve()
    output = args.output.resolve()
    terminal = root / "terminal64.exe"
    metaeditor = root / "MetaEditor64.exe"
    if not all(path.exists() for path in (EA_SOURCE, terminal, metaeditor)):
        raise FileNotFoundError("R6 source or isolated MT5 binary missing")

    experts = root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target = experts / EA_SOURCE.name
    shutil.copy2(EA_SOURCE, target)
    compile_log = root / "Logs" / "compile_A1XauR6OwnerDirectedSingleEventBacktest.log"
    compile_log.parent.mkdir(parents=True, exist_ok=True)
    compile_result = subprocess.run(
        [str(metaeditor), f"/compile:{target}", f"/log:{compile_log}"],
        capture_output=True, text=True, timeout=120, check=False,
    )
    ex5 = target.with_suffix(".ex5")
    compile_text = read_text(compile_log) if compile_log.exists() else ""
    if not ex5.exists() or ("error(s)" in compile_text.lower() and "0 error(s)" not in compile_text.lower()):
        raise RuntimeError(f"R6 MT5 compile failed (exit {compile_result.returncode}):\n{compile_text}")

    report_base = args.report_base
    report = root / "Reports" / f"{report_base}.htm"
    for suffix in (".htm", ".png", "-holding.png", "-mfemae.png", "-hst.png"):
        candidate = root / "Reports" / f"{report_base}{suffix}"
        if candidate.exists():
            candidate.unlink()
    config = root / "Config" / f"{report_base}.ini"
    config.write_text(
        "\n".join(
            [
                "[Common]", "Login=1025742", "Server=Capital.ComMena-Demo", "KeepPrivate=1", "NewsEnable=0", "",
                "[Tester]", f"Expert={EA_NAME}.ex5", "Symbol=XAUUSD", "Period=M5", "Optimization=0",
                "Model=0", "Dates=2", f"FromDate={args.from_date}", f"ToDate={args.to_date}", "ForwardMode=0",
                "Deposit=1000", "Currency=USD", "ProfitInPips=0", "Leverage=50", "ExecutionMode=0",
                "OptimizationCriterion=0", "Visual=0", f"Report=Reports\\{report_base}", "ReplaceReport=1",
                "ShutdownTerminal=1", "UseLocal=1", "UseRemote=0", "UseCloud=0", "", "[TesterInputs]",
                "InpSignalTime=2024.08.30 17:00:00", "InpStructuralStop=2507.65", "InpRiskReward=2.00",
                "InpLots=0.01", "InpMagic=926001", "",
            ]
        ),
        encoding="utf-8",
    )

    started = datetime.now(timezone.utc)
    process = subprocess.Popen(
        [str(terminal), "/portable", f"/config:{config}"], cwd=str(root),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError("R6 single-event MT5 test timed out")
    if not report.exists():
        raise FileNotFoundError(f"MT5 report missing: {report}")

    rows = html_rows(report)
    metrics = report_metrics(rows)
    deals = deal_rows(rows)
    if int(re.sub(r"[^0-9]", "", metrics.get("Bars", "0")) or "0") <= 0:
        raise RuntimeError("MT5 produced no bars")
    output.mkdir(parents=True, exist_ok=True)
    copied_report = output / report.name
    copied_compile = output / compile_log.name
    copied_config = output / config.name
    shutil.copy2(report, copied_report)
    shutil.copy2(compile_log, copied_compile)
    shutil.copy2(config, copied_config)
    payload = {
        "schema_version": "a1_xau_r6_owner_directed_single_event_mt5_v1",
        "status": "DEVELOPMENT_ONLY_SINGLE_EVENT_NOT_QUALIFIED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
        "tester_root": str(root),
        "from_date": args.from_date,
        "to_date": args.to_date,
        "report": str(copied_report),
        "compile_log": str(copied_compile),
        "config": str(copied_config),
        "compile_exit_code": compile_result.returncode,
        "metrics": metrics,
        "deals": deals,
        "limitations": [
            "the decade locked detector found only one structural event",
            "the MT5 EA executes that frozen event timestamp rather than reimplementing the full detector",
            "one trade cannot establish expectancy, PF, win rate, or robustness",
            "no demo/live runtime or broker position was touched",
        ],
    }
    (output / f"{report_base}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# A1 XAU R6 owner-directed ten-year MT5 test", "",
        "Status: `DEVELOPMENT_ONLY_SINGLE_EVENT_NOT_QUALIFIED`", "",
        f"- Total trades: `{metrics.get('Total Trades', 'missing')}`",
        f"- Net profit: `{metrics.get('Total Net Profit', 'missing')}`",
        f"- Profit factor: `{metrics.get('Profit Factor', 'missing')}`",
        f"- Equity drawdown maximal: `{metrics.get('Equity Drawdown Maximal', 'missing')}`",
        f"- History quality: `{metrics.get('History Quality', 'missing')}`", "",
        "This ten-year run validates only the realized MT5 path of the sole locked R6 event. It rejects the locked R6 definition for insufficient incidence and cannot qualify R6.", "",
    ]
    (output / f"{report_base}.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
