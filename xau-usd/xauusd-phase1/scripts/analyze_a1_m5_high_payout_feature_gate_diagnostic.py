from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPO_ROOT,
    REPORTS_DIR,
    build_source_specs,
    dedupe_signals,
    load_sources,
    rel,
    sha256_file,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STEM = "A1_XAU_M5_HIGH_PAYOUT_FEATURE_GATE_DIAGNOSTIC_2026_07_05"
PREREG_PATH = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_M5_HIGH_PAYOUT_FEATURE_GATE_DIAGNOSTIC_PREREG_2026_07_05.md"
)

BASE_PORTFOLIOS: dict[str, tuple[str, ...]] = {
    "hp_core_orrev_simple": (
        "step1_f33_r30_be_never",
        "orrev_london_firm_stop10",
    ),
    "hp_core_v13_orrev": (
        "step1_f33_r30_be_never",
        "v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning",
        "orrev_london_firm_stop10",
    ),
    "hp_core_v13_v9_orrev": (
        "step1_f33_r30_be_never",
        "v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning",
        "v9_sweep_h1h4_long_rr2p0_v4mask",
        "orrev_london_firm_stop10",
    ),
}

FEATURES = (
    "spread_points",
    "atr",
    "body_fraction",
    "close_location",
    "three_bar_move_atr",
    "break_distance_atr",
    "estimated_cost_r",
    "signal_range",
    "recent_range",
    "close_to_recent_extreme",
    "against_wick_points",
    "against_wick_body_ratio",
)

QUANTILES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.70, 0.75, 0.80, 0.85, 0.90)


def parse_float(value: Any, default: float = math.nan) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def signal_csv_for_trade_csv(path: Path) -> Path:
    if path.name.endswith("_trades.csv"):
        return path.with_name(path.name.replace("_trades.csv", "_signals.csv"))
    return path.with_name(path.stem + "_signals.csv")


def signal_key(entry_time: datetime, direction: str) -> tuple[str, str]:
    return entry_time.strftime("%Y.%m.%d %H:%M:%S"), str(direction).upper()


def wanted_signal_keys(trades: list[dict[str, Any]]) -> dict[str, set[tuple[str, str]]]:
    wanted: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in trades:
        source_csv = str(row.get("source_csv") or "")
        if not source_csv:
            continue
        wanted[source_csv].add(signal_key(row["entry_time"], row["direction"]))
    return wanted


def open_signal_reader(path: Path) -> tuple[Any, csv.DictReader]:
    handle = path.open(newline="", encoding="utf-8-sig")
    sample = handle.read(4096)
    handle.seek(0)
    delimiter = "\t" if "\t" in sample.splitlines()[0] else ","
    return handle, csv.DictReader(handle, delimiter=delimiter)


def parse_signal_features(row: dict[str, str]) -> dict[str, float]:
    open_ = parse_float(row.get("signal_open"))
    high = parse_float(row.get("signal_high"))
    low = parse_float(row.get("signal_low"))
    close = parse_float(row.get("signal_close"))
    recent_high = parse_float(row.get("recent_high"))
    recent_low = parse_float(row.get("recent_low"))
    direction = str(row.get("direction", "")).upper()

    body = abs(close - open_) if all(not math.isnan(v) for v in (close, open_)) else math.nan
    upper_wick = high - max(open_, close) if all(not math.isnan(v) for v in (high, open_, close)) else math.nan
    lower_wick = min(open_, close) - low if all(not math.isnan(v) for v in (low, open_, close)) else math.nan
    against_wick = upper_wick if direction == "LONG" else lower_wick if direction == "SHORT" else math.nan
    close_to_extreme = (
        close - recent_high
        if direction == "LONG"
        else recent_low - close
        if direction == "SHORT"
        else math.nan
    )

    return {
        "spread_points": parse_float(row.get("spread_points")),
        "atr": parse_float(row.get("atr")),
        "body_fraction": parse_float(row.get("body_fraction")),
        "close_location": parse_float(row.get("close_location")),
        "three_bar_move_atr": parse_float(row.get("three_bar_move_atr")),
        "break_distance_atr": parse_float(row.get("break_distance_atr")),
        "estimated_cost_r": parse_float(row.get("estimated_cost_r")),
        "signal_range": high - low if all(not math.isnan(v) for v in (high, low)) else math.nan,
        "recent_range": recent_high - recent_low
        if all(not math.isnan(v) for v in (recent_high, recent_low))
        else math.nan,
        "close_to_recent_extreme": close_to_extreme,
        "against_wick_points": against_wick,
        "against_wick_body_ratio": against_wick / body if body and body > 0 else math.nan,
    }


def load_signal_features(
    trades: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str, str], dict[str, float]], list[dict[str, Any]]]:
    wanted = wanted_signal_keys(trades)
    features: dict[tuple[str, str, str], dict[str, float]] = {}
    inventory: list[dict[str, Any]] = []

    for source_csv, keys in sorted(wanted.items()):
        trade_path = Path(source_csv)
        signal_path = signal_csv_for_trade_csv(trade_path)
        item = {
            "source_csv": source_csv,
            "signal_csv": str(signal_path),
            "exists": signal_path.exists(),
            "wanted": len(keys),
            "matched": 0,
            "sha256": sha256_file(signal_path) if signal_path.exists() else "",
        }
        if not signal_path.exists():
            inventory.append(item)
            continue

        handle, reader = open_signal_reader(signal_path)
        with handle:
            for row in reader:
                if str(row.get("stage", "")).upper() != "WOULD_SIGNAL":
                    continue
                key = (str(row.get("timestamp_broker", "")), str(row.get("direction", "")).upper())
                if key not in keys:
                    continue
                features[(source_csv, key[0], key[1])] = parse_signal_features(row)
        item["matched"] = sum(1 for key in keys if (source_csv, key[0], key[1]) in features)
        inventory.append(item)

    return features, inventory


def enrich_trades(
    trades: list[dict[str, Any]],
    signal_features: dict[tuple[str, str, str], dict[str, float]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in trades:
        copied = dict(row)
        key_time, key_direction = signal_key(row["entry_time"], row["direction"])
        feature_row = signal_features.get((str(row.get("source_csv") or ""), key_time, key_direction), {})
        copied.update(feature_row)
        copied["feature_joined"] = bool(feature_row)
        enriched.append(copied)
    return enriched


def quantile_thresholds(values: list[float]) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 50:
        return []
    thresholds: list[float] = []
    last_index = len(clean) - 1
    for quantile in QUANTILES:
        index = max(0, min(last_index, round(last_index * quantile)))
        thresholds.append(round(clean[index], 6))
    return sorted(set(thresholds))


def matches_rule(row: dict[str, Any], feature: str, op: str, threshold: float, direction: str) -> bool:
    if direction != "ANY" and str(row.get("direction", "")).upper() != direction:
        return False
    value = parse_float(row.get(feature))
    if math.isnan(value):
        return False
    return value <= threshold if op == "<=" else value >= threshold


def apply_rule(
    trades: list[dict[str, Any]],
    feature: str,
    op: str,
    threshold: float,
    direction: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in trades:
        if matches_rule(row, feature, op, threshold, direction):
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def classify(row: dict[str, Any]) -> str:
    retention = float(row.get("retention_pct") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    win_loss = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    pf = float(row.get("profit_factor") or 0.0)

    if retention < 50.0:
        return "FAIL_RETENTION"
    if net <= 0.0:
        return "FAIL_NET"
    if win_loss < 2.0:
        return "FAIL_WIN_LOSS"
    if wr >= 50.0 and active >= 90.0:
        return "OWNER_DIAGNOSTIC_HIT"
    if wr >= 50.0 and active >= 50.0:
        return "CORE_SHAPE_REPLAY_CANDIDATE"
    if wr >= 47.5 and active >= 50.0 and pf >= 1.40:
        return "NEAR_OWNER_REPLAY_CANDIDATE"
    if wr < 47.5:
        return "FAIL_WIN_RATE"
    return "FAIL_ACTIVE_COVERAGE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.25) * 350
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.5) * 275
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.2) * 225
        + min(float(row.get("profit_factor") or 0.0) / 1.4, 1.5) * 125
        + min(float(row.get("retention_pct") or 0.0) / 100.0, 1.0) * 75,
        4,
    )


def build_base_trades() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    specs = build_source_specs()
    sources, inventory = load_sources(specs)
    base_trades: dict[str, list[dict[str, Any]]] = {}
    for base_name, source_ids in BASE_PORTFOLIOS.items():
        raw: list[dict[str, Any]] = []
        for source_id in source_ids:
            raw.extend(sources[source_id])
        kept, _dropped = dedupe_signals(raw)
        base_trades[base_name] = kept
    return base_trades, inventory


def evaluate_base(base_name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(trades, market_days=MARKET_DAYS)
    metrics.update(
        {
            "base": base_name,
            "rule": "BASELINE",
            "feature": "",
            "op": "",
            "threshold": "",
            "direction_filter": "",
            "blocked_signals": 0,
            "blocked_net_usd": 0.0,
            "retention_pct": 100.0,
            "decision": classify({**metrics, "retention_pct": 100.0}),
        }
    )
    metrics["score"] = score(metrics)
    return metrics


def evaluate_rule(
    base_name: str,
    feature: str,
    op: str,
    threshold: float,
    direction: str,
    base_count: int,
    kept: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    blocked_net = sum(float(row.get("pnl_usd") or 0.0) for row in blocked)
    metrics.update(
        {
            "base": base_name,
            "rule": f"{direction} {feature} {op} {threshold}",
            "feature": feature,
            "op": op,
            "threshold": threshold,
            "direction_filter": direction,
            "blocked_signals": len(blocked),
            "blocked_net_usd": round(blocked_net, 2),
            "retention_pct": round(100.0 * len(kept) / base_count, 2) if base_count else 0.0,
        }
    )
    metrics["decision"] = classify(metrics)
    metrics["score"] = score(metrics)
    return metrics


def search_feature_rules(
    base_name: str,
    trades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [evaluate_base(base_name, trades)]
    feature_joined = [row for row in trades if row.get("feature_joined")]
    for feature in FEATURES:
        for direction in ("ANY", "LONG", "SHORT"):
            scoped = [
                row
                for row in feature_joined
                if direction == "ANY" or str(row.get("direction", "")).upper() == direction
            ]
            thresholds = quantile_thresholds([parse_float(row.get(feature)) for row in scoped])
            for threshold in thresholds:
                for op in ("<=", ">="):
                    kept, blocked = apply_rule(trades, feature, op, threshold, direction)
                    if not blocked:
                        continue
                    rows.append(evaluate_rule(base_name, feature, op, threshold, direction, len(trades), kept, blocked))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    keys = [
        "decision",
        "score",
        "base",
        "rule",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "net_usd",
        "profit_factor",
        "retention_pct",
        "blocked_signals",
        "blocked_net_usd",
        "active_weekdays",
        "signals_per_active_day",
        "positive_months",
        "negative_months",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
        "feature",
        "op",
        "threshold",
        "direction_filter",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    best = payload["best_row"]
    lines = [
        "# A1 XAU M5 High-Payout Feature-Gate Diagnostic",
        "",
        "Generated: 2026-07-05",
        "",
        "Scope: offline exact-MT5 trade/signal CSV diagnostic only. No MT5 launch, runtime attach, charts, presets, orders, or broker state mutation.",
        "",
        f"Decision: **{payload['status']}**",
        "",
        "Reviewer spend rule: preserve the daily reviewer pass unless an exact-MT5 replay validates a candidate. This diagnostic alone is not review-worthy.",
        "",
        "## Best Row",
        "",
        f"- Base: `{best.get('base')}`",
        f"- Rule: `{best.get('rule')}`",
        f"- Decision: `{best.get('decision')}`",
        f"- Signals: {best.get('signals')}",
        f"- WR: {best.get('win_rate_pct')}%",
        f"- Avg win / avg loss: {best.get('avg_win_loss')}",
        f"- Active weekdays: {best.get('active_weekdays')} / {len(MARKET_DAYS)} ({best.get('active_weekday_pct')}%)",
        f"- Net: {best.get('net_usd')}",
        f"- PF: {best.get('profit_factor')}",
        f"- Retention: {best.get('retention_pct')}%",
        f"- Blocked: {best.get('blocked_signals')} signals / {best.get('blocked_net_usd')} USD",
        "",
        "## Base Metrics",
        "",
        "| Base | Signals | WR % | W/L | Active % | Net | PF | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["base_rows"]:
        lines.append(
            f"| `{row['base']}` | {row['signals']} | {row['win_rate_pct']} | {row['avg_win_loss']} | "
            f"{row['active_weekday_pct']} | {row['net_usd']} | {row['profit_factor']} | `{row['decision']}` |"
        )

    lines.extend(
        [
            "",
            "## Top Diagnostic Rows",
            "",
            "| Rank | Decision | Base | Rule | Signals | WR % | W/L | Active % | Net | PF | Retention % | Blocked net |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {rank} | `{row['decision']}` | `{row['base']}` | `{row['rule']}` | {row['signals']} | "
            f"{row['win_rate_pct']} | {row['avg_win_loss']} | {row['active_weekday_pct']} | {row['net_usd']} | "
            f"{row['profit_factor']} | {row['retention_pct']} | {row['blocked_net_usd']} |"
        )

    lines.extend(
        [
            "",
            "## Signal Join Inventory",
            "",
            "| Signal CSV | Wanted | Matched | Exists | SHA256 |",
            "|---|---:|---:|---|---|",
        ]
    )
    for item in payload["signal_inventory"]:
        lines.append(
            f"| `{rel(Path(item['signal_csv']))}` | {item['wanted']} | {item['matched']} | "
            f"{item['exists']} | `{str(item['sha256'])[:12]}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            f"CSV: `{rel(Path(payload['outputs']['csv']))}`",
            f"JSON: `{rel(Path(payload['outputs']['json']))}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    base_trades, source_inventory = build_base_trades()
    all_base_rows = []
    all_result_rows: list[dict[str, Any]] = []
    signal_inventory_by_csv: dict[str, dict[str, Any]] = {}

    for base_name, trades in base_trades.items():
        signal_features, signal_inventory = load_signal_features(trades)
        for item in signal_inventory:
            existing = signal_inventory_by_csv.get(item["signal_csv"])
            if existing is None:
                signal_inventory_by_csv[item["signal_csv"]] = item
            else:
                existing["wanted"] += item["wanted"]
                existing["matched"] += item["matched"]
        enriched = enrich_trades(trades, signal_features)
        rows = search_feature_rules(base_name, enriched)
        all_result_rows.extend(rows)
        all_base_rows.append(rows[0])

    decision_rank = {
        "OWNER_DIAGNOSTIC_HIT": 5,
        "CORE_SHAPE_REPLAY_CANDIDATE": 4,
        "NEAR_OWNER_REPLAY_CANDIDATE": 3,
        "FAIL_ACTIVE_COVERAGE": 2,
        "FAIL_WIN_RATE": 1,
        "FAIL_WIN_LOSS": 1,
        "FAIL_NET": 0,
        "FAIL_RETENTION": 0,
    }
    all_result_rows.sort(
        key=lambda row: (
            decision_rank.get(str(row.get("decision")), -1),
            row.get("score") or 0.0,
            row.get("win_rate_pct") or 0.0,
            row.get("avg_win_loss") or 0.0,
            row.get("active_weekday_pct") or 0.0,
            row.get("net_usd") or 0.0,
        ),
        reverse=True,
    )
    best = all_result_rows[0] if all_result_rows else {}
    candidate_decisions = {
        "OWNER_DIAGNOSTIC_HIT",
        "CORE_SHAPE_REPLAY_CANDIDATE",
        "NEAR_OWNER_REPLAY_CANDIDATE",
    }
    candidates = [row for row in all_result_rows if row.get("decision") in candidate_decisions]
    status = "DIAGNOSTIC_REJECT_NO_REPLAY_CANDIDATE"
    interpretation = (
        "No single signal-feature block moved the high-payout exact-MT5 frontier close enough to justify "
        "an exact MT5 replay. Preserve reviewer budget and move to a different premise."
    )
    if candidates:
        status = "DIAGNOSTIC_REPLAY_CANDIDATE_FOUND"
        interpretation = (
            "At least one offline feature block reached the replay threshold. This is not promotable by itself; "
            "the next step is a default-off EA implementation and exact MT5 replay of the frozen rule."
        )

    csv_path = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    payload = {
        "status": status,
        "generated": "2026-07-05",
        "boundary": "offline_exact_mt5_trade_signal_csv_diagnostic_only_no_mt5_launch",
        "preregistration": str(PREREG_PATH),
        "base_portfolios": BASE_PORTFOLIOS,
        "best_row": best,
        "candidate_rows": candidates[:20],
        "base_rows": all_base_rows,
        "top_rows": all_result_rows[:25],
        "signal_inventory": sorted(signal_inventory_by_csv.values(), key=lambda item: item["signal_csv"]),
        "source_inventory": source_inventory,
        "interpretation": interpretation,
        "outputs": {
            "csv": str(csv_path),
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }

    write_csv(csv_path, all_result_rows)
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": status, "best_decision": best.get("decision"), "report": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
