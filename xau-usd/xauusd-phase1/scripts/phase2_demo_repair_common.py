from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY = Path("config") / "phase2_demo_repair_policy.yaml"
DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_WEAKNESS_JSON = Path("outputs") / "reports" / "PHASE2_EA_WEAKNESS_SHADOW_REPORT.json"

LIST_KEYS = {"suspend_candidates", "disable_symbols", "observer_only_candidates", "keep_candidates"}
MAP_KEYS = {"p2weakness"}
LIST_OF_MAP_KEYS = {"conditional_session_blocks_shadow"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_policy(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    policy: dict[str, Any] = {}
    current_key: str | None = None
    current_item: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            current_item = None
            if value:
                policy[key] = parse_scalar(value)
            elif key in LIST_KEYS:
                policy[key] = []
            elif key in MAP_KEYS:
                policy[key] = {}
            elif key in LIST_OF_MAP_KEYS:
                policy[key] = []
            else:
                policy[key] = {}
            continue
        if current_key in LIST_KEYS and line.startswith("- "):
            policy.setdefault(current_key, []).append(parse_scalar(line[2:].strip()))
            continue
        if current_key in LIST_OF_MAP_KEYS and line.startswith("- "):
            current_item = {}
            policy.setdefault(current_key, []).append(current_item)
            remainder = line[2:].strip()
            if ":" in remainder:
                key, value = remainder.split(":", 1)
                current_item[key.strip()] = parse_scalar(value.strip())
            continue
        if current_key in LIST_OF_MAP_KEYS and current_item is not None and ":" in line:
            key, value = line.split(":", 1)
            current_item[key.strip()] = parse_scalar(value.strip())
            continue
        if current_key in MAP_KEYS and ":" in line:
            key, value = line.split(":", 1)
            policy.setdefault(current_key, {})[key.strip()] = parse_scalar(value.strip())
    return policy


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_trades(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [normalize_trade(row) for row in csv.DictReader(handle)]


def latest_weekly_unique_csv(report_dir: Path) -> Path | None:
    candidates = sorted(report_dir.glob("PHASE2_DEMO_WEEKLY_UNIQUE_TRADES_*.csv"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def select_trade_source(root: Path) -> Path:
    weekly = latest_weekly_unique_csv(root / "outputs" / "reports")
    return weekly if weekly else root / DEFAULT_ACTUAL_TRADES


def normalize_trade(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["profit_value"] = to_float(enriched.get("profit_aed"))
    enriched["volume_value"] = to_float(enriched.get("volume"))
    enriched["magic_value"] = to_int(enriched.get("magic"))
    enriched["is_duplicate_value"] = is_true(enriched.get("is_duplicate"))
    enriched["time_bucket"] = enriched.get("time_bucket") or time_bucket(enriched.get("entry_time", ""))
    enriched["entry_dt"] = parse_dt(enriched.get("entry_time"))
    return enriched


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            pass
    return None


def time_bucket(entry_time: Any) -> str:
    text = str(entry_time or "")
    try:
        hour = int(text[11:13])
    except (TypeError, ValueError):
        return "UNKNOWN"
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def to_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def duplicate_hidden(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row.get("is_duplicate_value")]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if str(row.get("state", "")).upper() == "CLOSED"]
    open_rows = [row for row in rows if str(row.get("state", "")).upper() == "OPEN"]
    wins = [row for row in closed if row["profit_value"] > 0]
    losses = [row for row in closed if row["profit_value"] < 0]
    gross_win = sum(row["profit_value"] for row in wins)
    gross_loss = sum(row["profit_value"] for row in losses)
    closed_pnl = sum(row["profit_value"] for row in closed)
    floating_pnl = sum(row["profit_value"] for row in open_rows)
    pf = gross_win / abs(gross_loss) if gross_loss else (999999.0 if gross_win else None)
    return {
        "actual_trades": len(rows),
        "closed_trades": len(closed),
        "open_trades": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "closed_win_rate_pct": round(len(wins) / (len(wins) + len(losses)) * 100.0, 2) if wins or losses else None,
        "closed_pnl_aed": round(closed_pnl, 2),
        "floating_pnl_aed": round(floating_pnl, 2),
        "total_pnl_aed": round(closed_pnl + floating_pnl, 2),
        "profit_factor": "inf" if pf == 999999.0 else (round(pf, 2) if pf is not None else None),
        "profit_factor_value": pf or 0.0,
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
        "max_volume": max([row.get("volume_value", 0.0) for row in rows], default=0.0),
    }


def grouped_summaries(rows: list[dict[str, Any]], keys: list[str], policy: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in keys)
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key, group_rows in grouped.items():
        summary = summarize(group_rows)
        for index, field in enumerate(keys):
            summary[field] = key[index]
        classification, reason = classify_bucket(
            candidate=str(summary.get("candidate", "")),
            symbol=str(summary.get("symbol", "")),
            time_bucket=str(summary.get("time_bucket", "")),
            max_volume=float(summary.get("max_volume", 0.0)),
            policy=policy,
        )
        summary["classification"] = classification
        summary["reason"] = reason
        output.append(summary)
    return sorted(output, key=lambda item: (str(item.get("candidate", "")), str(item.get("symbol", "")), str(item.get("time_bucket", ""))))


def classify_bucket(
    *,
    candidate: str,
    symbol: str,
    time_bucket: str,
    max_volume: float,
    policy: dict[str, Any],
) -> tuple[str, str]:
    disabled_symbols = set(policy.get("disable_symbols", []))
    suspend_candidates = set(policy.get("suspend_candidates", []))
    observer_only = set(policy.get("observer_only_candidates", []))
    keep = set(policy.get("keep_candidates", []))
    if symbol in disabled_symbols:
        return "DISABLED_SYMBOL", f"{symbol} is disabled by repair policy."
    if candidate in suspend_candidates:
        return "SUSPEND_NO_NEW_ENTRIES", f"{candidate} is suspended for new demo entries."
    if symbol == "EURUSD":
        if max_volume >= 0.05:
            return "OWNER_REVIEW_REQUIRED", "EURUSD 0.05 exposure requires owner risk acceptance."
        return "OWNER_REVIEW_REQUIRED", "EURUSD experimental exposure is under owner lot-size review."
    if candidate in observer_only:
        return "OBSERVER_ONLY", f"{candidate} is observer-only under the repair policy."
    if session_block_applies(symbol, time_bucket, policy):
        return "REDUCE_DEMO", "XAUUSD morning/afternoon remains a shadow-forward block candidate."
    if candidate in keep:
        return "KEEP_DEMO", f"{candidate} remains controlled demo candidate."
    return "REDUCE_DEMO", "No explicit keep approval; keep measuring or reduce exposure."


def session_block_applies(symbol: str, time_bucket_value: str, policy: dict[str, Any]) -> bool:
    if symbol != "XAUUSD":
        return False
    for block in policy.get("conditional_session_blocks_shadow", []):
        if block.get("symbol") != symbol:
            continue
        if time_bucket_value.startswith("Morning") or time_bucket_value.startswith("Afternoon"):
            return True
    return False


def rows_since(rows: list[dict[str, Any]], since_text: str | None) -> list[dict[str, Any]]:
    if not since_text:
        return rows
    since = parse_dt(since_text)
    if since is None:
        return rows
    return [row for row in rows if row.get("entry_dt") and row["entry_dt"] >= since]


def rows_before(rows: list[dict[str, Any]], since_text: str | None) -> list[dict[str, Any]]:
    if not since_text:
        return []
    since = parse_dt(since_text)
    if since is None:
        return []
    return [row for row in rows if row.get("entry_dt") and row["entry_dt"] < since]


def fmt(value: Any, pct: bool = False) -> str:
    if value is None:
        return "n/a"
    if value == "inf":
        return "inf"
    if isinstance(value, str):
        return value
    suffix = "%" if pct else ""
    return f"{float(value):.2f}{suffix}"


def metrics_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
    lines = [
        "| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in rows:
        lines.append(
            f"| {label} | {summary['actual_trades']} | {summary['closed_trades']} | {summary['open_trades']} | "
            f"{summary['wins']} | {summary['losses']} | {fmt(summary['closed_win_rate_pct'], pct=True)} | "
            f"{fmt(summary['closed_pnl_aed'])} | {fmt(summary['floating_pnl_aed'])} | {fmt(summary['total_pnl_aed'])} | "
            f"{fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
        )
    return "\n".join(lines)


def bucket_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Candidate | Symbol | Time Bucket | Class | Closed | Win Rate | PnL | PF | Reason |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('candidate', '')} | {row.get('symbol', '')} | {row.get('time_bucket', '')} | "
            f"{row.get('classification', '')} | {row.get('closed_trades', 0)} | "
            f"{fmt(row.get('closed_win_rate_pct'), pct=True)} | {fmt(row.get('closed_pnl_aed'))} | "
            f"{fmt(row.get('profit_factor'))} | {row.get('reason', '')} |"
        )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
