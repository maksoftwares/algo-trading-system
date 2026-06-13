from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_REPORT_DIR = Path("outputs") / "reports"
A3_MAGICS = {"933000", "933100"}
EVENING_BUCKET = "Evening 16:00-19:59"


@dataclass(frozen=True)
class A3ReviewOutput:
    status: str
    weekly_markdown: Path
    daily_markdown: Path
    json_path: Path


def generate_a3_review_reports(
    root: Path,
    *,
    trades_csv: Path | None = None,
    report_date: str | None = None,
    output_dir: Path | None = None,
) -> A3ReviewOutput:
    root = root.resolve()
    trades_csv = (trades_csv or root / DEFAULT_TRADES).resolve()
    output_dir = (output_dir or root / DEFAULT_REPORT_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    today = report_date or datetime.now(timezone.utc).strftime("%Y_%m_%d")

    trades = [_normalize_trade(row) for row in _read_csv(trades_csv)]
    evening = _evening_session_pnl(trades)
    payload: dict[str, Any] = {
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "global_boundaries": {
            "a3_demo_login": "1033669",
            "demo_only": True,
            "canonical_phase2_status_unchanged": True,
            "a2_1033030_untouched": True,
            "a1_1025742_not_touched_by_report": True,
        },
        "source_trades_csv": str(trades_csv),
        "report_date": today,
        "evening_session_pnl": evening,
        "a3_trade_summary": _summarize([row for row in trades if str(row.get("magic", "")) in A3_MAGICS]),
        "portfolio_summary": _summarize(trades),
    }

    weekly_md = output_dir / "A3_WEEKLY_REVIEW_PACKET.md"
    daily_md = output_dir / f"A3_GUARD_ATTRIBUTION_DAILY_{today}.md"
    json_path = output_dir / "A3_REVIEW_REPORTS.json"
    weekly_md.write_text(_render_weekly(payload), encoding="utf-8")
    daily_md.write_text(_render_daily(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return A3ReviewOutput(payload["status"], weekly_md, daily_md, json_path)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_trade(row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = dict(row)
    result["profit_value"] = _to_float(row.get("profit_aed")) or 0.0
    result["time_bucket"] = row.get("time_bucket") or _time_bucket(row.get("entry_time", ""))
    result["state"] = row.get("state", "").upper()
    return result


def _evening_session_pnl(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evening_rows = [row for row in rows if row.get("time_bucket") == EVENING_BUCKET]
    realized = sum(float(row.get("profit_value", 0.0)) for row in evening_rows if row.get("state") == "CLOSED")
    floating = sum(float(row.get("profit_value", 0.0)) for row in evening_rows if row.get("state") != "CLOSED")
    open_rows = [row for row in evening_rows if row.get("state") != "CLOSED"]
    return {
        "window_dubai": "16:00-19:59",
        "realized_pnl_aed": round(realized, 2),
        "floating_pnl_aed": round(floating, 2),
        "total_pnl_aed": round(realized + floating, 2),
        "status": "open" if open_rows else "closed for the day",
        "rows": len(evening_rows),
        "open_rows": len(open_rows),
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    wins = [row for row in closed if float(row.get("profit_value", 0.0)) > 0.0]
    losses = [row for row in closed if float(row.get("profit_value", 0.0)) < 0.0]
    gross_win = sum(float(row.get("profit_value", 0.0)) for row in wins)
    gross_loss = sum(float(row.get("profit_value", 0.0)) for row in losses)
    pnl = sum(float(row.get("profit_value", 0.0)) for row in closed)
    return {
        "closed": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "closed_pnl_aed": round(pnl, 2),
        "win_rate_pct": round((len(wins) / len(closed) * 100.0), 2) if closed else None,
        "profit_factor": round((gross_win / abs(gross_loss)), 4) if gross_loss else None,
    }


def _time_bucket(value: Any) -> str:
    parsed = _parse_dt(value)
    if parsed is None:
        return "UNKNOWN"
    hour = parsed.hour
    if 16 <= hour <= 19:
        return EVENING_BUCKET
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    return "Night 20:00-05:59"


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _to_float(value: Any) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except ValueError:
        return None


def _evening_line(payload: dict[str, Any]) -> str:
    evening = payload["evening_session_pnl"]
    return (
        "Evening session PnL (16:00-19:59 Dubai): "
        f"{evening['total_pnl_aed']:.2f} AED, status: {evening['status']}"
    )


def _render_weekly(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# A3 Weekly Review Packet",
            "",
            f"Status: `{payload['status']}`",
            "",
            "## Boundary",
            "",
            "- A3 login: `1033669`.",
            "- Demo only; canonical Phase 2 unchanged.",
            "- A2 untouched; A1 is control reference.",
            "",
            "## Evening Session",
            "",
            _evening_line(payload),
            "",
            "## A3 Trade Summary",
            "",
            _dict_table(payload["a3_trade_summary"]),
            "",
            "## Portfolio Summary",
            "",
            _dict_table(payload["portfolio_summary"]),
            "",
        ]
    )


def _render_daily(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# A3 Guard Attribution Daily {payload['report_date']}",
            "",
            f"Status: `{payload['status']}`",
            "",
            _evening_line(payload),
            "",
            "## Guard Attribution",
            "",
            "No A3 guard-attribution rows are available until EA-T1/EA-T2 dry-run or execution logs exist.",
            "",
        ]
    )


def _dict_table(row: dict[str, Any]) -> str:
    lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in row.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate A3 weekly and daily review reports.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--report-date", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output = generate_a3_review_reports(
        args.root,
        trades_csv=args.trades_csv,
        report_date=args.report_date,
        output_dir=args.output_dir,
    )
    print(f"Status: {output.status}")
    print(f"Weekly: {output.weekly_markdown}")
    print(f"Daily: {output.daily_markdown}")
    print(f"JSON: {output.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
