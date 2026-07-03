from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_OUTPUT_CSV = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_M5_MOMENTUM_RR2_ATTRIBUTION_EXPORT_2026_07_02.csv"
RUN_ID = "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702"
ACCOUNT_LOGIN = "1025742"
MAGIC = 932200
LANE_START = datetime(2026, 7, 2, 4, 46, 42)


def export_a1_momentum_rr2_attribution(
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
) -> dict[str, Any]:
    terminal_exe = terminal_exe.resolve()
    output_csv = output_csv.resolve()
    output_md = output_csv.with_suffix(".md")
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    payload = query_deals(terminal_exe)
    account = payload.get("account") or {}
    if str(account.get("login")) != ACCOUNT_LOGIN:
        raise RuntimeError(f"Expected A1 login {ACCOUNT_LOGIN}, got {account}")

    rows = []
    for deal in payload.get("deals", []):
        deal_time = datetime.fromtimestamp(int(deal["time"]))
        phase = "RR2_FORWARD" if deal_time >= LANE_START else "PRE_SPEC_EXCLUDED"
        rows.append(
            {
                "phase": phase,
                "time_broker": deal_time.strftime("%Y-%m-%d %H:%M:%S"),
                "ticket": deal.get("ticket", 0),
                "position_id": deal.get("position_id", 0),
                "order": deal.get("order", 0),
                "symbol": deal.get("symbol", ""),
                "magic": deal.get("magic", 0),
                "type": deal.get("type", 0),
                "entry": deal.get("entry", 0),
                "volume": deal.get("volume", 0.0),
                "price": deal.get("price", 0.0),
                "profit": deal.get("profit", 0.0),
                "commission": deal.get("commission", 0.0),
                "swap": deal.get("swap", 0.0),
                "fee": deal.get("fee", 0.0),
                "net": round(
                    float(deal.get("profit", 0.0))
                    + float(deal.get("commission", 0.0))
                    + float(deal.get("swap", 0.0))
                    + float(deal.get("fee", 0.0)),
                    2,
                ),
                "comment": deal.get("comment", ""),
                "external_id": deal.get("external_id", ""),
            }
        )

    fieldnames = [
        "phase",
        "time_broker",
        "ticket",
        "position_id",
        "order",
        "symbol",
        "magic",
        "type",
        "entry",
        "volume",
        "price",
        "profit",
        "commission",
        "swap",
        "fee",
        "net",
        "comment",
        "external_id",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    output_md.write_text(render_markdown(output_csv, terminal_exe, account, rows, summary), encoding="utf-8")
    return {
        "status": "PASS",
        "output_csv": str(output_csv),
        "output_md": str(output_md),
        "account": account,
        "summary": summary,
    }


def query_deals(terminal_exe: Path) -> dict[str, Any]:
    start = LANE_START.replace(hour=0, minute=0, second=0) - timedelta(days=1)
    end = datetime.now() + timedelta(days=1)
    script = f"""
import json
from datetime import datetime
import MetaTrader5 as mt5
path = r'{terminal_exe}'
if not mt5.initialize(path=path):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    account = mt5.account_info()
    deals = mt5.history_deals_get(datetime({start.year},{start.month},{start.day},{start.hour},{start.minute},{start.second}), datetime({end.year},{end.month},{end.day},{end.hour},{end.minute},{end.second})) or []
    filtered = []
    for deal in deals:
        item = deal._asdict()
        if int(item.get('magic') or 0) == {MAGIC}:
            filtered.append(item)
    print(json.dumps({{
        'account': account._asdict() if account else {{}},
        'deals': filtered,
        'last_error': str(mt5.last_error()),
    }}, default=str))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(venv_python()), "-c", script], text=True, capture_output=True, timeout=45)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 deal export failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def venv_python() -> Path:
    return PHASE1_ROOT.parent / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    phases = {}
    for row in rows:
        phase = str(row["phase"])
        phases.setdefault(phase, {"deals": 0, "net": 0.0, "positions": set()})
        phases[phase]["deals"] += 1
        phases[phase]["net"] += float(row["net"])
        phases[phase]["positions"].add(str(row["position_id"]))
    return {
        phase: {
            "deals": item["deals"],
            "positions": len(item["positions"]),
            "net": round(item["net"], 2),
        }
        for phase, item in sorted(phases.items())
    }


def render_markdown(
    output_csv: Path,
    terminal_exe: Path,
    account: dict[str, Any],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# A1 XAU M5 Momentum RR2 Attribution Export - 2026-07-02",
        "",
        "Status: `PASS`",
        "",
        "Purpose: pin magic `932200` attribution after reusing the same magic/comment for the July 1 pre-spec lane.",
        "",
        f"- Terminal: `{terminal_exe}`",
        f"- Account: `{account.get('login')}` / `{account.get('server')}`",
        f"- Forward run id: `{RUN_ID}`",
        f"- Forward start broker time: `{LANE_START:%Y-%m-%d %H:%M:%S}`",
        f"- CSV: `{output_csv}`",
        "",
        "## Summary",
        "",
        "| Phase | Deals | Positions | Net |",
        "|---|---:|---:|---:|",
    ]
    if summary:
        for phase, item in summary.items():
            lines.append(f"| `{phase}` | {item['deals']} | {item['positions']} | {item['net']:.2f} |")
    else:
        lines.append("| `NO_932200_DEALS_FOUND` | 0 | 0 | 0.00 |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `PRE_SPEC_EXCLUDED` rows belong to the previous July 1 directional-session momentum lane and are excluded from RR2 forward scoring.",
            "- `RR2_FORWARD` rows are eligible for the locked RR2 long-only forward test.",
            "- Net is `profit + commission + swap + fee` from actual MT5 deal history.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()
    result = export_a1_momentum_rr2_attribution(args.terminal_exe, args.output_csv)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
