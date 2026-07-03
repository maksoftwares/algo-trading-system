"""Analyze realized demo trades and XAU signal factors.

This report intentionally separates evidence levels:

1. Legacy all-symbol broker table, if present.
2. Fresh C02 multi-account XAU broker history exported from MT5 read-only.
3. C01 XAU feature snapshot rows, which are diagnostic signal labels rather
   than a replacement for realized broker fills.

No MT5 terminal is touched by this script.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
REPORTS = PHASE1_ROOT / "outputs" / "reports"

LEGACY_ACTUAL_TRADES = REPORTS / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
C02_POINTER = REPORTS / "C02_DATASET_POINTER.json"
C01_SNAPSHOT_ROWS = REPORTS / "A3_ML_C01_SNAPSHOT_ROWS.csv"

OUT_MD = REPORTS / "DEMO_TRADE_FACTOR_COMMONALITY_2026_06_27.md"
OUT_JSON = REPORTS / "DEMO_TRADE_FACTOR_COMMONALITY_2026_06_27.json"
OUT_FEATURES = REPORTS / "DEMO_TRADE_FACTOR_COMMONALITY_FEATURE_STATS_2026_06_27.csv"
OUT_THRESHOLDS = REPORTS / "DEMO_TRADE_FACTOR_COMMONALITY_THRESHOLDS_2026_06_27.csv"


MAGIC_NAMES = {
    "920101": "breakout_retest",
    "920201": "swing_breakout_retest_v0",
    "920301": "symbol_normalized_round_retest_v0",
    "920401": "round_number_retest_v0",
    "920501": "session_extreme_retest_v0",
    "920504": "session_extreme_retest_v0",
    "921101": "symbol_normalized_round_retest_v0_repair_v1",
    "921201": "session_extreme_retest_v0_repair_v1",
    "930101": "p2weakness_br_v1",
    "931000": "phase2x_owner_authorized_br",
    "933100": "a3_structure_guard",
    "933200": "a3_breakout_plain",
    "933300": "a3_breakout_improved",
    "933400": "a3_breakout_tier1_compat",
    "933500": "soft_retest_v2",
}


FEATURE_COLUMNS = [
    "h1_ema20_slope_aligned_atr",
    "m15_ema20_slope_aligned_atr",
    "d1_trend_score_aligned",
    "price_h1_ema20_distance_aligned_atr",
    "break_distance_atr",
    "confirmation_body_ratio",
    "confirmation_close_location_aligned",
    "impulse_alignment_12",
    "range_compression_ratio_20",
    "tick_volume_ratio_20",
    "m5_atr_percentile_trailing_20d",
    "spread_percentile_session_trailing_20d",
    "bars_break_to_retest_scaled",
    "minutes_from_session_start_scaled",
    "cost_R",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: object, default: float = math.nan) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        return default


def to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if text == "":
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def fmt_money(value: float) -> str:
    return f"{value:,.2f}"


def fmt_pct(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value * 100:.1f}%"


def fmt_num(value: float, digits: int = 3) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def profit_factor(profits: Iterable[float]) -> float:
    wins = sum(p for p in profits if p > 0)
    losses = -sum(p for p in profits if p < 0)
    if losses == 0:
        return math.inf if wins > 0 else math.nan
    return wins / losses


def mean(values: list[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    if not vals:
        return math.nan
    return sum(vals) / len(vals)


def median(values: list[float]) -> float:
    vals = sorted(v for v in values if not math.isnan(v))
    if not vals:
        return math.nan
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2


def stdev(values: list[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    if len(vals) < 2:
        return math.nan
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def percentile(values: list[float], p: float) -> float:
    vals = sorted(v for v in values if not math.isnan(v))
    if not vals:
        return math.nan
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def summarize_profit_rows(rows: list[dict[str, object]], profit_key: str = "profit_aed") -> dict[str, object]:
    profits = [to_float(row.get(profit_key)) for row in rows]
    profits = [p for p in profits if not math.isnan(p)]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    return {
        "trades": len(profits),
        "wins": len(wins),
        "losses": len(losses),
        "flats": len([p for p in profits if p == 0]),
        "win_rate": (len(wins) / (len(wins) + len(losses))) if wins or losses else math.nan,
        "pnl": sum(profits),
        "avg_win": mean(wins),
        "avg_loss": mean(losses),
        "profit_factor": profit_factor(profits),
    }


def group_summary(rows: list[dict[str, object]], keys: list[str], profit_key: str = "profit_aed") -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(normalize_text(row.get(key)) or "UNKNOWN" for key in keys)].append(row)
    out = []
    for key_values, group_rows in grouped.items():
        s = summarize_profit_rows(group_rows, profit_key)
        rec = {key: value for key, value in zip(keys, key_values)}
        rec.update(s)
        out.append(rec)
    out.sort(key=lambda r: (to_float(r.get("pnl")), to_int(r.get("trades"))), reverse=True)
    return out


def table(rows: list[dict[str, object]], columns: list[tuple[str, str]], limit: int | None = None) -> str:
    shown = rows[:limit] if limit else rows
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in shown:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                if key in {"win_rate"}:
                    value = fmt_pct(value)
                elif key in {"pnl", "avg_win", "avg_loss"}:
                    value = fmt_money(value)
                elif key in {"profit_factor"}:
                    value = "inf" if math.isinf(value) else fmt_num(value, 2)
                else:
                    value = fmt_num(value, 3)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def dubai_bucket_from_utc(dt: datetime | None) -> str:
    if dt is None:
        return "UNKNOWN"
    hour = (dt.hour + 4) % 24
    if 6 <= hour <= 11:
        return "MORNING"
    if 12 <= hour <= 15:
        return "AFTERNOON"
    if 16 <= hour <= 19:
        return "EVENING"
    return "NIGHT"


def parse_epoch_time(value: object) -> datetime | None:
    try:
        raw = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if raw <= 0:
        return None
    return datetime.fromtimestamp(raw, tz=timezone.utc)


def parse_time_text(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def load_legacy_all_symbol() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = read_csv(LEGACY_ACTUAL_TRADES)
    out: list[dict[str, object]] = []
    for row in rows:
        state = normalize_text(row.get("state"))
        if state and state.upper() not in {"CLOSED", "DONE", "FILLED"}:
            continue
        rec: dict[str, object] = dict(row)
        rec["profit_aed"] = to_float(row.get("profit_aed"))
        rec["volume"] = to_float(row.get("volume"))
        rec["is_duplicate"] = normalize_text(row.get("is_duplicate")).lower() == "true"
        rec["symbol"] = normalize_text(row.get("symbol"))
        rec["candidate"] = normalize_text(row.get("candidate") or row.get("entry_comment") or row.get("magic"))
        rec["direction"] = normalize_text(row.get("direction"))
        rec["time_bucket"] = normalize_text(row.get("time_bucket")) or dubai_bucket_from_utc(parse_time_text(row.get("entry_time")))
        rec["magic"] = normalize_text(row.get("magic"))
        out.append(rec)
    meta = {
        "path": str(LEGACY_ACTUAL_TRADES),
        "rows": len(out),
        "exists": LEGACY_ACTUAL_TRADES.exists(),
    }
    return out, meta


def c02_dataset_root() -> Path | None:
    if not C02_POINTER.exists():
        return None
    with C02_POINTER.open("r", encoding="utf-8") as handle:
        pointer = json.load(handle)
    root = pointer.get("output_root")
    if not root:
        return None
    path = Path(root)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def load_fresh_c02_xau_trades() -> tuple[list[dict[str, object]], dict[str, object]]:
    root = c02_dataset_root()
    if root is None:
        return [], {"exists": False, "reason": "C02_DATASET_POINTER.json missing"}

    rows: list[dict[str, object]] = []
    accounts_root = root / "raw"
    for account_dir in sorted(accounts_root.glob("A*/history")):
        account_label = account_dir.parent.name
        deals = read_csv(account_dir / "deals.csv")
        if not deals:
            continue
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for deal in deals:
            position_id = normalize_text(deal.get("position_id") or deal.get("position"))
            if not position_id or position_id == "0":
                continue
            grouped[position_id].append(deal)

        for position_id, deal_rows in grouped.items():
            deal_rows.sort(key=lambda r: to_float(r.get("time"), 0))
            entry_rows = [r for r in deal_rows if to_int(r.get("entry"), -1) == 0]
            exit_rows = [r for r in deal_rows if to_int(r.get("entry"), -1) != 0]
            if not entry_rows or not exit_rows:
                continue
            entry = entry_rows[0]
            exit_deal = exit_rows[-1]
            entry_dt = parse_epoch_time(entry.get("time"))
            exit_dt = parse_epoch_time(exit_deal.get("time"))
            magic = normalize_text(entry.get("magic"))
            direction_type = to_int(entry.get("type"), -1)
            direction = "BUY" if direction_type == 0 else "SELL" if direction_type == 1 else normalize_text(entry.get("type"))
            profit = 0.0
            for deal in deal_rows:
                profit += to_float(deal.get("profit"), 0.0)
                profit += to_float(deal.get("commission"), 0.0)
                profit += to_float(deal.get("swap"), 0.0)
                profit += to_float(deal.get("fee"), 0.0)
            rows.append(
                {
                    "account_label": account_label,
                    "account_scope": normalize_text(entry.get("account_scope")),
                    "symbol": normalize_text(entry.get("symbol")),
                    "candidate": MAGIC_NAMES.get(magic, normalize_text(entry.get("comment")) or magic),
                    "magic": magic,
                    "direction": direction,
                    "volume": to_float(entry.get("volume")),
                    "entry_time_utc": entry_dt.isoformat() if entry_dt else "",
                    "exit_time_utc": exit_dt.isoformat() if exit_dt else "",
                    "time_bucket": dubai_bucket_from_utc(entry_dt),
                    "entry_price": to_float(entry.get("price")),
                    "exit_price": to_float(exit_deal.get("price")),
                    "profit_aed": profit,
                    "position_id": position_id,
                    "entry_comment": normalize_text(entry.get("comment")),
                    "exit_comment": normalize_text(exit_deal.get("comment")),
                }
            )
    meta = {
        "exists": True,
        "dataset_root": str(root),
        "rows": len(rows),
        "accounts": sorted({normalize_text(r.get("account_label")) for r in rows}),
        "symbols": sorted({normalize_text(r.get("symbol")) for r in rows}),
    }
    return rows, meta


def load_snapshot_rows() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = read_csv(C01_SNAPSHOT_ROWS)
    out: list[dict[str, object]] = []
    for row in rows:
        label = to_float(row.get("y_win_expected"))
        if math.isnan(label):
            continue
        rec: dict[str, object] = dict(row)
        rec["y_win_expected"] = 1 if label >= 0.5 else 0
        rec["y_net_R_expected"] = to_float(row.get("y_net_R_expected"))
        rec["y_net_R_p95_stress"] = to_float(row.get("y_net_R_p95_stress"))
        rec["account_label"] = normalize_text(row.get("account_label"))
        rec["session_bucket"] = normalize_text(row.get("session_bucket"))
        rec["direction"] = normalize_text(row.get("direction"))
        rec["regime"] = normalize_text(row.get("regime"))
        for feature in FEATURE_COLUMNS:
            rec[feature] = to_float(row.get(feature))
        out.append(rec)
    meta = {
        "path": str(C01_SNAPSHOT_ROWS),
        "rows": len(out),
        "exists": C01_SNAPSHOT_ROWS.exists(),
    }
    return out, meta


def feature_stats(snapshot_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    wins = [row for row in snapshot_rows if row["y_win_expected"] == 1]
    losses = [row for row in snapshot_rows if row["y_win_expected"] == 0]
    rows: list[dict[str, object]] = []
    for feature in FEATURE_COLUMNS:
        win_vals = [to_float(row.get(feature)) for row in wins]
        loss_vals = [to_float(row.get(feature)) for row in losses]
        win_vals = [v for v in win_vals if not math.isnan(v)]
        loss_vals = [v for v in loss_vals if not math.isnan(v)]
        if len(win_vals) + len(loss_vals) < 30:
            continue
        pooled = math.nan
        if len(win_vals) > 1 and len(loss_vals) > 1:
            sw = stdev(win_vals)
            sl = stdev(loss_vals)
            if not math.isnan(sw) and not math.isnan(sl):
                pooled = math.sqrt(((len(win_vals) - 1) * sw * sw + (len(loss_vals) - 1) * sl * sl) / (len(win_vals) + len(loss_vals) - 2))
        diff = mean(win_vals) - mean(loss_vals)
        effect = diff / pooled if pooled and not math.isnan(pooled) else math.nan
        rows.append(
            {
                "feature": feature,
                "winner_n": len(win_vals),
                "loser_n": len(loss_vals),
                "winner_mean": mean(win_vals),
                "loser_mean": mean(loss_vals),
                "winner_median": median(win_vals),
                "loser_median": median(loss_vals),
                "mean_diff_win_minus_loss": diff,
                "effect_size": effect,
                "winner_p25": percentile(win_vals, 0.25),
                "winner_p75": percentile(win_vals, 0.75),
                "loser_p25": percentile(loss_vals, 0.25),
                "loser_p75": percentile(loss_vals, 0.75),
            }
        )
    rows.sort(key=lambda r: abs(to_float(r.get("effect_size"))), reverse=True)
    return rows


def threshold_scan(snapshot_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    base_win_rate = mean([to_float(row.get("y_win_expected")) for row in snapshot_rows])
    base_net_r = mean([to_float(row.get("y_net_R_expected")) for row in snapshot_rows])
    rows: list[dict[str, object]] = []
    for feature in FEATURE_COLUMNS:
        values = [to_float(row.get(feature)) for row in snapshot_rows]
        values = [v for v in values if not math.isnan(v)]
        if len(values) < 50:
            continue
        candidates = sorted({percentile(values, q) for q in (0.2, 0.25, 0.33, 0.5, 0.67, 0.75, 0.8)})
        for threshold in candidates:
            for op in ("<=", ">="):
                if op == "<=":
                    subset = [row for row in snapshot_rows if not math.isnan(to_float(row.get(feature))) and to_float(row.get(feature)) <= threshold]
                else:
                    subset = [row for row in snapshot_rows if not math.isnan(to_float(row.get(feature))) and to_float(row.get(feature)) >= threshold]
                if len(subset) < 30:
                    continue
                win_rate = mean([to_float(row.get("y_win_expected")) for row in subset])
                net_r = mean([to_float(row.get("y_net_R_expected")) for row in subset])
                stress_r = mean([to_float(row.get("y_net_R_p95_stress")) for row in subset])
                rows.append(
                    {
                        "feature": feature,
                        "rule": f"{feature} {op} {threshold:.6g}",
                        "threshold": threshold,
                        "operator": op,
                        "n": len(subset),
                        "retention": len(subset) / len(snapshot_rows) if snapshot_rows else math.nan,
                        "win_rate": win_rate,
                        "win_rate_lift": win_rate - base_win_rate,
                        "net_R_mean": net_r,
                        "net_R_lift": net_r - base_net_r,
                        "p95_stress_R_mean": stress_r,
                    }
                )
    rows.sort(key=lambda r: (to_float(r.get("win_rate_lift")), to_float(r.get("net_R_lift"))), reverse=True)
    return rows


def label_group_summary(snapshot_rows: list[dict[str, object]], keys: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in snapshot_rows:
        grouped[tuple(normalize_text(row.get(key)) or "UNKNOWN" for key in keys)].append(row)
    rows: list[dict[str, object]] = []
    for key_values, group_rows in grouped.items():
        win_rate = mean([to_float(row.get("y_win_expected")) for row in group_rows])
        net_r = mean([to_float(row.get("y_net_R_expected")) for row in group_rows])
        stress_r = mean([to_float(row.get("y_net_R_p95_stress")) for row in group_rows])
        rec = {key: value for key, value in zip(keys, key_values)}
        rec.update(
            {
                "signals": len(group_rows),
                "wins": sum(1 for row in group_rows if row["y_win_expected"] == 1),
                "losses": sum(1 for row in group_rows if row["y_win_expected"] == 0),
                "win_rate": win_rate,
                "net_R_mean": net_r,
                "p95_stress_R_mean": stress_r,
            }
        )
        rows.append(rec)
    rows.sort(key=lambda r: (to_float(r.get("net_R_mean")), to_float(r.get("signals"))), reverse=True)
    return rows


def top_and_bottom(rows: list[dict[str, object]], key: str, n: int = 8) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sorted_rows = sorted(rows, key=lambda r: to_float(r.get(key)), reverse=True)
    return sorted_rows[:n], list(reversed(sorted_rows[-n:]))


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    legacy_rows, legacy_meta = load_legacy_all_symbol()
    legacy_dedup = [row for row in legacy_rows if not row.get("is_duplicate")]
    fresh_xau_rows, fresh_xau_meta = load_fresh_c02_xau_trades()
    snapshot_rows, snapshot_meta = load_snapshot_rows()

    fstats = feature_stats(snapshot_rows)
    thresholds = threshold_scan(snapshot_rows)
    write_csv(
        OUT_FEATURES,
        fstats,
        [
            "feature",
            "winner_n",
            "loser_n",
            "winner_mean",
            "loser_mean",
            "winner_median",
            "loser_median",
            "mean_diff_win_minus_loss",
            "effect_size",
            "winner_p25",
            "winner_p75",
            "loser_p25",
            "loser_p75",
        ],
    )
    write_csv(
        OUT_THRESHOLDS,
        thresholds,
        [
            "feature",
            "rule",
            "threshold",
            "operator",
            "n",
            "retention",
            "win_rate",
            "win_rate_lift",
            "net_R_mean",
            "net_R_lift",
            "p95_stress_R_mean",
        ],
    )

    legacy_summary = {
        "raw": summarize_profit_rows(legacy_rows),
        "duplicate_hidden": summarize_profit_rows(legacy_dedup),
        "by_symbol_dedup": group_summary(legacy_dedup, ["symbol"]),
        "by_candidate_dedup": group_summary(legacy_dedup, ["candidate"]),
        "by_session_dedup": group_summary(legacy_dedup, ["time_bucket"]),
        "by_symbol_session_dedup": group_summary(legacy_dedup, ["symbol", "time_bucket"]),
    }
    fresh_xau_summary = {
        "all": summarize_profit_rows(fresh_xau_rows),
        "by_account": group_summary(fresh_xau_rows, ["account_label"]),
        "by_account_candidate": group_summary(fresh_xau_rows, ["account_label", "candidate"]),
        "by_session": group_summary(fresh_xau_rows, ["time_bucket"]),
        "by_account_session": group_summary(fresh_xau_rows, ["account_label", "time_bucket"]),
        "by_direction": group_summary(fresh_xau_rows, ["direction"]),
    }
    label_summary = {
        "all": {
            "signals": len(snapshot_rows),
            "wins": sum(1 for row in snapshot_rows if row["y_win_expected"] == 1),
            "losses": sum(1 for row in snapshot_rows if row["y_win_expected"] == 0),
            "win_rate": mean([to_float(row.get("y_win_expected")) for row in snapshot_rows]),
            "net_R_mean": mean([to_float(row.get("y_net_R_expected")) for row in snapshot_rows]),
            "p95_stress_R_mean": mean([to_float(row.get("y_net_R_p95_stress")) for row in snapshot_rows]),
        },
        "by_account": label_group_summary(snapshot_rows, ["account_label"]),
        "by_session": label_group_summary(snapshot_rows, ["session_bucket"]),
        "by_direction": label_group_summary(snapshot_rows, ["direction"]),
        "by_regime": label_group_summary(snapshot_rows, ["regime"]),
        "by_account_session": label_group_summary(snapshot_rows, ["account_label", "session_bucket"]),
    }

    top_features = fstats[:10]
    top_thresholds = thresholds[:12]
    good_groups, bad_groups = top_and_bottom(label_summary["by_account_session"], "net_R_mean", 8)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = []
    lines.append("# Demo Trade Factor Commonality Analysis")
    lines.append("")
    lines.append(f"Generated UTC: `{now}`")
    lines.append("")
    lines.append("## Evidence Boundary")
    lines.append("")
    lines.append("- Legacy all-symbol broker fills are read from `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`; this table is useful for broad symbol/EA/session patterns but is older than the latest C02 export.")
    lines.append("- Fresh C02 broker history is multi-account but currently XAUUSD-only, exported read-only from MT5 for A1/A2/A3.")
    lines.append("- Numeric EMA/ATR/volume/trend factors come from `A3_ML_C01_SNAPSHOT_ROWS.csv`; these are diagnostic signal labels, not proof that a filter is deployable.")
    lines.append("- No MT5 terminal, chart, order, preset, or EA runtime was modified.")
    lines.append("")

    lines.append("## Realized Broker Fills: Legacy All-Symbol View")
    lines.append("")
    lines.append(f"Source: `{legacy_meta['path']}`")
    lines.append(f"Rows used: `{legacy_meta['rows']}`")
    lines.append("")
    lines.append(table([legacy_summary["raw"], legacy_summary["duplicate_hidden"]], [("trades", "Trades"), ("wins", "Wins"), ("losses", "Losses"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("### Duplicate-Hidden By Symbol")
    lines.append(table(legacy_summary["by_symbol_dedup"], [("symbol", "Symbol"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")], 12))
    lines.append("")
    lines.append("### Duplicate-Hidden By Candidate")
    lines.append(table(legacy_summary["by_candidate_dedup"], [("candidate", "EA/Candidate"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")], 16))
    lines.append("")
    lines.append("### Duplicate-Hidden By Dubai Session")
    lines.append(table(legacy_summary["by_session_dedup"], [("time_bucket", "Session"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")

    lines.append("## Fresh Realized XAUUSD Broker Fills: Multi-Account C02 View")
    lines.append("")
    lines.append(f"Dataset root: `{fresh_xau_meta.get('dataset_root', '')}`")
    lines.append(f"Rows used: `{fresh_xau_meta.get('rows', 0)}`")
    lines.append(f"Accounts: `{', '.join(fresh_xau_meta.get('accounts', []))}`")
    lines.append("")
    lines.append(table([fresh_xau_summary["all"]], [("trades", "Trades"), ("wins", "Wins"), ("losses", "Losses"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("### XAUUSD By Account")
    lines.append(table(fresh_xau_summary["by_account"], [("account_label", "Account"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("### XAUUSD By Account And Candidate")
    lines.append(table(fresh_xau_summary["by_account_candidate"], [("account_label", "Account"), ("candidate", "EA/Candidate"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")], 20))
    lines.append("")
    lines.append("### XAUUSD By Dubai Session")
    lines.append(table(fresh_xau_summary["by_session"], [("time_bucket", "Session"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")

    lines.append("## XAUUSD Signal Feature Split: Winners Vs Losers")
    lines.append("")
    lines.append(f"Source: `{snapshot_meta['path']}`")
    lines.append(f"Rows used: `{snapshot_meta['rows']}`")
    lines.append("")
    lines.append(table([label_summary["all"]], [("signals", "Signals"), ("wins", "Expected Wins"), ("losses", "Expected Losses"), ("win_rate", "WR"), ("net_R_mean", "Mean R"), ("p95_stress_R_mean", "P95 Stress R")]))
    lines.append("")
    lines.append("### Strongest Numeric Separators")
    lines.append(table(top_features, [("feature", "Feature"), ("winner_n", "Win N"), ("loser_n", "Loss N"), ("winner_mean", "Win Mean"), ("loser_mean", "Loss Mean"), ("winner_median", "Win Median"), ("loser_median", "Loss Median"), ("mean_diff_win_minus_loss", "Mean Diff"), ("effect_size", "Effect")], 10))
    lines.append("")
    lines.append("### Best One-Factor Diagnostic Thresholds")
    lines.append(table(top_thresholds, [("rule", "Rule"), ("n", "Signals"), ("retention", "Retention"), ("win_rate", "WR"), ("win_rate_lift", "WR Lift"), ("net_R_mean", "Mean R"), ("p95_stress_R_mean", "Stress R")], 12))
    lines.append("")
    lines.append("### Feature-Label Result By Account And Session")
    lines.append("Best cells:")
    lines.append(table(good_groups, [("account_label", "Account"), ("session_bucket", "Session"), ("signals", "Signals"), ("win_rate", "WR"), ("net_R_mean", "Mean R"), ("p95_stress_R_mean", "Stress R")]))
    lines.append("")
    lines.append("Worst cells:")
    lines.append(table(bad_groups, [("account_label", "Account"), ("session_bucket", "Session"), ("signals", "Signals"), ("win_rate", "WR"), ("net_R_mean", "Mean R"), ("p95_stress_R_mean", "Stress R")]))
    lines.append("")
    lines.append("## Practical Reading")
    lines.append("")
    lines.append("- Treat the broker-fill tables as money truth and the feature tables as diagnostics for what to test next.")
    lines.append("- A factor is interesting only when it improves realized or broker-joined performance out of sample; these single-factor cuts are not deployment rules.")
    lines.append("- The safest immediate use is to look for repeated loser fingerprints: bad account/session/candidate clusters, high cost_R, weak trend alignment, poor confirmation candle quality, high spread percentile, and range-compression conditions.")
    lines.append("- Any proposed filter from this report should be locked as a forward-test hypothesis before touching runtime.")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- Feature stats CSV: `{OUT_FEATURES}`")
    lines.append(f"- Threshold scan CSV: `{OUT_THRESHOLDS}`")
    lines.append(f"- Machine summary JSON: `{OUT_JSON}`")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "generated_utc": now,
        "inputs": {
            "legacy_actual_trades": legacy_meta,
            "fresh_c02_xau": fresh_xau_meta,
            "c01_snapshot_rows": snapshot_meta,
        },
        "legacy_all_symbol": legacy_summary,
        "fresh_xau": fresh_xau_summary,
        "xau_signal_labels": label_summary,
        "top_feature_separators": top_features[:20],
        "top_thresholds": top_thresholds[:25],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, allow_nan=True), encoding="utf-8")

    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_FEATURES}")
    print(f"Wrote {OUT_THRESHOLDS}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
