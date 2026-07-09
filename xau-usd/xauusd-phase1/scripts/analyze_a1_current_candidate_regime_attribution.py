from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709"

REGIME_DAYS = REPORTS_DIR / "A1_XAU_10Y_REGIME_MAP_20260709_DAYS.csv"

R1_CURRENT = REPORTS_DIR / "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv"
R2_PULLBACK = REPORTS_DIR / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv"
R2_CONTINUATION = REPORTS_DIR / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_daily_loss10_NORMALIZED_TRADES.csv"
R2_COMBINED = REPORTS_DIR / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
R3_COMPRESSION = REPORTS_DIR / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv"
R3_COMBINED = REPORTS_DIR / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035_KEPT.csv"
R4_CHOP_BOTH = REPORTS_DIR / "A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_r4_chop_prior_day_reclaim_v1_both_NORMALIZED_TRADES.csv"
R4_COMBINED = REPORTS_DIR / "A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_both_KEPT.csv"

RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)
REGIME_ORDER = ["uptrend", "downtrend", "chop", "compression", "shock", "transition", "unknown", "missing"]


BOOK_SPECS = [
    {"book": "R1_current_long_book", "path": R1_CURRENT, "class": "R1", "priority": 20},
    {"book": "R2_pullback_short_v2_hours05_18", "path": R2_PULLBACK, "class": "R2", "priority": 10},
    {"book": "R2_continuation_short_v4_atr45_daily_loss10", "path": R2_CONTINUATION, "class": "R2", "priority": 11},
    {"book": "R2_combined_current_best", "path": R2_COMBINED, "class": "combined", "priority": 5},
    {"book": "R3_compression_long_v1", "path": R3_COMPRESSION, "class": "R3", "priority": 30},
    {"book": "R3_combined_with_R1", "path": R3_COMBINED, "class": "combined", "priority": 6},
    {"book": "R4_chop_prior_day_reclaim_both", "path": R4_CHOP_BOTH, "class": "R4", "priority": 40},
    {"book": "R4_combined_with_R1", "path": R4_COMBINED, "class": "combined", "priority": 7},
]

FILTER_TESTS = [
    {"test": "R1_prev_uptrend_only", "source": "R1_current_long_book", "allowed": {"uptrend"}},
    {"test": "R1_prev_uptrend_or_shock", "source": "R1_current_long_book", "allowed": {"uptrend", "shock"}},
    {"test": "R2_pullback_prev_downtrend_only", "source": "R2_pullback_short_v2_hours05_18", "allowed": {"downtrend"}},
    {"test": "R2_pullback_prev_downtrend_or_transition", "source": "R2_pullback_short_v2_hours05_18", "allowed": {"downtrend", "transition"}},
    {"test": "R2_cont_prev_downtrend_only", "source": "R2_continuation_short_v4_atr45_daily_loss10", "allowed": {"downtrend"}},
    {"test": "R2_cont_prev_downtrend_or_transition", "source": "R2_continuation_short_v4_atr45_daily_loss10", "allowed": {"downtrend", "transition"}},
    {"test": "R3_prev_compression_only", "source": "R3_compression_long_v1", "allowed": {"compression"}},
    {"test": "R3_prev_compression_or_chop", "source": "R3_compression_long_v1", "allowed": {"compression", "chop"}},
    {"test": "R4_prev_chop_only", "source": "R4_chop_prior_day_reclaim_both", "allowed": {"chop"}},
    {"test": "R4_prev_chop_or_compression", "source": "R4_chop_prior_day_reclaim_both", "allowed": {"chop", "compression"}},
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PHASE1_ROOT.parents[1]))
    except ValueError:
        return str(path)


def load_regime_maps() -> tuple[dict[date, str], dict[date, str]]:
    frame = pd.read_csv(REGIME_DAYS)
    frame["date"] = pd.to_datetime(frame["date"]).dt.date
    frame = frame.sort_values("date")
    same_day = dict(zip(frame["date"], frame["regime"]))
    prev_day: dict[date, str] = {}
    previous = "missing"
    for day, regime in zip(frame["date"], frame["regime"]):
        prev_day[day] = previous
        previous = str(regime)
    return same_day, prev_day


def previous_regime_for(entry_day: date, sorted_days: list[date], same_day: dict[date, str]) -> str:
    # Use the most recent completed D1 row strictly before the entry date.
    idx = np.searchsorted(np.array(sorted_days, dtype=object), entry_day) - 1
    if idx < 0:
        return "missing"
    return str(same_day.get(sorted_days[idx], "missing"))


def load_book(spec: dict[str, Any], same_day: dict[date, str]) -> pd.DataFrame:
    path = Path(spec["path"])
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if frame.empty:
        frame["book"] = spec["book"]
        return frame
    frame["book"] = spec["book"]
    frame["book_class"] = spec["class"]
    frame["portfolio_priority"] = spec["priority"]
    frame["entry_dt"] = pd.to_datetime(frame["entry_time"], errors="coerce")
    frame["exit_dt"] = pd.to_datetime(frame["exit_time"], errors="coerce")
    frame["entry_day"] = pd.to_datetime(frame["entry_date"], errors="coerce").dt.date
    frame["pnl_usd"] = pd.to_numeric(frame["pnl_usd"], errors="coerce").fillna(0.0)
    frame["tickets"] = pd.to_numeric(frame.get("tickets", 1), errors="coerce").fillna(1).astype(int)
    if "component" not in frame.columns:
        frame["component"] = spec["book"]
    if "source_id" not in frame.columns:
        frame["source_id"] = frame["component"]
    sorted_days = sorted(same_day)
    frame["same_day_regime"] = frame["entry_day"].map(same_day).fillna("missing")
    frame["prev_d1_regime"] = frame["entry_day"].apply(lambda item: previous_regime_for(item, sorted_days, same_day))
    frame["recent3"] = frame["entry_day"].apply(lambda item: RECENT3_START <= item <= RECENT3_END if pd.notna(item) else False)
    frame["month"] = frame["entry_day"].apply(lambda item: f"{item.year:04d}-{item.month:02d}" if pd.notna(item) else "")
    frame["dedupe_key"] = (
        frame["entry_time"].astype(str)
        + "|"
        + frame.get("direction", "").astype(str)
        + "|"
        + frame["component"].astype(str)
    )
    return frame


def max_closed_drawdown(rows: pd.DataFrame) -> float:
    if rows.empty:
        return 0.0
    ordered = rows.sort_values(["exit_dt", "entry_dt"], na_position="last")
    equity = ordered["pnl_usd"].cumsum()
    peak = equity.cummax()
    dd = peak - equity
    return round(float(dd.max()), 2) if len(dd) else 0.0


def metrics(rows: pd.DataFrame, name: str = "") -> dict[str, Any]:
    wins = rows[rows["pnl_usd"] > 0.0]
    losses = rows[rows["pnl_usd"] < 0.0]
    gross_profit = float(wins["pnl_usd"].sum()) if not wins.empty else 0.0
    gross_loss = abs(float(losses["pnl_usd"].sum())) if not losses.empty else 0.0
    avg_win = float(wins["pnl_usd"].mean()) if not wins.empty else 0.0
    avg_loss = abs(float(losses["pnl_usd"].mean())) if not losses.empty else 0.0
    stressed = rows.copy()
    if not stressed.empty:
        stressed["pnl_usd"] = stressed["pnl_usd"] - 0.30 * stressed["tickets"]
    swins = stressed[stressed["pnl_usd"] > 0.0]
    slosses = stressed[stressed["pnl_usd"] < 0.0]
    sgp = float(swins["pnl_usd"].sum()) if not swins.empty else 0.0
    sgl = abs(float(slosses["pnl_usd"].sum())) if not slosses.empty else 0.0
    months = rows.groupby("month")["pnl_usd"].sum() if not rows.empty else pd.Series(dtype=float)
    return {
        "name": name,
        "trades": int(len(rows)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "wr_pct": round(100.0 * len(wins) / (len(wins) + len(losses)), 2) if len(wins) + len(losses) else 0.0,
        "wl": round(avg_win / avg_loss, 4) if avg_loss else 0.0,
        "pf": round(gross_profit / gross_loss, 4) if gross_loss else 0.0,
        "net": round(float(rows["pnl_usd"].sum()) if not rows.empty else 0.0, 2),
        "stress_net_030": round(float(stressed["pnl_usd"].sum()) if not stressed.empty else 0.0, 2),
        "stress_pf_030": round(sgp / sgl, 4) if sgl else 0.0,
        "max_closed_dd": max_closed_drawdown(rows),
        "recent3_trades": int(rows["recent3"].sum()) if "recent3" in rows else 0,
        "recent3_net": round(float(rows.loc[rows["recent3"], "pnl_usd"].sum()) if "recent3" in rows else 0.0, 2),
        "positive_months": int((months > 0.0).sum()),
        "negative_months": int((months < 0.0).sum()),
    }


def by_regime(rows: pd.DataFrame, group_name: str, group_value: str, regime_col: str = "prev_d1_regime") -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for regime in REGIME_ORDER:
        subset = rows[rows[regime_col] == regime]
        row = metrics(subset, regime)
        row[group_name] = group_value
        row["regime_basis"] = regime_col
        row["regime"] = regime
        output.append(row)
    return output


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = list(rows)
    if not data:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in data:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def dedupe_portfolio(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    frame = rows.copy()
    frame["portfolio_dedupe_key"] = frame["entry_time"].astype(str) + "|" + frame.get("direction", "").astype(str)
    frame = frame.sort_values(["portfolio_dedupe_key", "portfolio_priority", "pnl_usd"], ascending=[True, True, False])
    return frame.drop_duplicates("portfolio_dedupe_key", keep="first").copy()


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Current Candidate Regime Attribution",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: recomposition/audit of existing exact-MT5 trade ledgers against the 10-year D1 regime map. "
        "This is not a fresh MT5 backtest and does not prove a deployable filter by itself.",
        "",
        "Causal filter tests use `prev_d1_regime`, the most recent completed D1 regime strictly before entry date. "
        "This avoids same-day close lookahead.",
        "",
        "## Book Summary",
        "",
        "| Book | Trades | WR% | W/L | PF | Net | Stress Net | Recent3 Trades | Recent3 Net | Max DD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["book_rows"]:
        lines.append(
            f"| `{row['book']}` | {row['trades']} | {row['wr_pct']:.2f} | {row['wl']:.4f} | "
            f"{row['pf']:.4f} | {row['net']:.2f} | {row['stress_net_030']:.2f} | "
            f"{row['recent3_trades']} | {row['recent3_net']:.2f} | {row['max_closed_dd']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Regime Attribution By Book",
            "",
            "| Book | Prev D1 Regime | Trades | WR% | PF | Net | Recent3 Net |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["regime_rows"]:
        if row["trades"] == 0:
            continue
        lines.append(
            f"| `{row['book']}` | `{row['regime']}` | {row['trades']} | {row['wr_pct']:.2f} | "
            f"{row['pf']:.4f} | {row['net']:.2f} | {row['recent3_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Causal Regime Filter Tests",
            "",
            "| Test | Allowed Prev D1 Regimes | Kept / Base | WR% | PF | Net | Net Delta | Recent3 Net |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["filter_rows"]:
        lines.append(
            f"| `{row['test']}` | `{row['allowed_regimes']}` | {row['trades']} / {row['base_trades']} | "
            f"{row['wr_pct']:.2f} | {row['pf']:.4f} | {row['net']:.2f} | {row['net_delta']:.2f} | "
            f"{row['recent3_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Router Overlay Portfolios",
            "",
            "| Portfolio | Components | Trades | WR% | W/L | PF | Net | Stress Net | Recent3 Trades | Recent3 Net |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["portfolio_rows"]:
        lines.append(
            f"| `{row['portfolio']}` | {row['components']} | {row['trades']} | {row['wr_pct']:.2f} | "
            f"{row['wl']:.4f} | {row['pf']:.4f} | {row['net']:.2f} | {row['stress_net_030']:.2f} | "
            f"{row['recent3_trades']} | {row['recent3_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["decision"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    same_day, _prev = load_regime_maps()
    books: dict[str, pd.DataFrame] = {spec["book"]: load_book(spec, same_day) for spec in BOOK_SPECS}

    book_rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    tagged_frames: list[pd.DataFrame] = []
    for spec in BOOK_SPECS:
        frame = books[spec["book"]]
        tagged_frames.append(frame)
        row = metrics(frame, spec["book"])
        row["book"] = spec["book"]
        row["path"] = rel(spec["path"])
        book_rows.append(row)
        for item in by_regime(frame, "book", spec["book"]):
            regime_rows.append(item)

    filter_rows: list[dict[str, Any]] = []
    filtered_sources: dict[str, pd.DataFrame] = {}
    for test in FILTER_TESTS:
        base = books[test["source"]]
        allowed = set(test["allowed"])
        filtered = base[base["prev_d1_regime"].isin(allowed)].copy()
        filtered_sources[test["test"]] = filtered
        base_metrics = metrics(base, test["source"])
        row = metrics(filtered, test["test"])
        row["test"] = test["test"]
        row["source"] = test["source"]
        row["allowed_regimes"] = ",".join(sorted(allowed))
        row["base_trades"] = base_metrics["trades"]
        row["base_net"] = base_metrics["net"]
        row["net_delta"] = round(row["net"] - base_metrics["net"], 2)
        filter_rows.append(row)

    # Two practical overlays:
    # 1) strict specialists only in their named regime.
    # 2) tolerant transition-aware overlay for the recent chop/downtrend break.
    portfolio_defs = [
        {
            "portfolio": "baseline_R1_plus_R2_current_best",
            "components": "existing exact-MT5 combined R1+R2 pullback+R2 continuation",
            "frames": [books["R2_combined_current_best"]],
        },
        {
            "portfolio": "overlay_strict_named_regimes",
            "components": "R1 uptrend + R2 downtrend + R3 compression + R4 chop",
            "frames": [
                filtered_sources["R1_prev_uptrend_only"],
                filtered_sources["R2_pullback_prev_downtrend_only"],
                filtered_sources["R2_cont_prev_downtrend_only"],
                filtered_sources["R3_prev_compression_only"],
                filtered_sources["R4_prev_chop_only"],
            ],
        },
        {
            "portfolio": "overlay_transition_tolerant",
            "components": "R1 uptrend + R2 downtrend/transition + R3 compression/chop + R4 chop",
            "frames": [
                filtered_sources["R1_prev_uptrend_only"],
                filtered_sources["R2_pullback_prev_downtrend_or_transition"],
                filtered_sources["R2_cont_prev_downtrend_or_transition"],
                filtered_sources["R3_prev_compression_or_chop"],
                filtered_sources["R4_prev_chop_only"],
            ],
        },
        {
            "portfolio": "overlay_no_R4_transition_tolerant",
            "components": "R1 uptrend + R2 downtrend/transition + R3 compression/chop",
            "frames": [
                filtered_sources["R1_prev_uptrend_only"],
                filtered_sources["R2_pullback_prev_downtrend_or_transition"],
                filtered_sources["R2_cont_prev_downtrend_or_transition"],
                filtered_sources["R3_prev_compression_or_chop"],
            ],
        },
    ]
    portfolio_rows: list[dict[str, Any]] = []
    for item in portfolio_defs:
        rows = dedupe_portfolio(pd.concat(item["frames"], ignore_index=True)) if item["frames"] else pd.DataFrame()
        row = metrics(rows, item["portfolio"])
        row["portfolio"] = item["portfolio"]
        row["components"] = item["components"]
        portfolio_rows.append(row)

    decision = (
        "The D1 regime map helps diagnostically, but the naive previous-D1 overlay is not yet a deployable improvement. "
        "R1 remains strongest in uptrend but loses too much full-window profit if filtered by the coarse D1 label alone; "
        "R2's recent defense is real and is concentrated in transition/downtrend; R3 is strong historically but not active enough recently; "
        "R4 prior-day reclaim still does not earn its keep even inside chop. Next improvement should be a router audit using the EA's native intraday regime snapshot "
        "at each entry, then repair R4/chop rather than tightening R1 with this coarse daily classifier."
    )

    tagged_path = REPORTS_DIR / f"{OUTPUT_STEM}_TAGGED_TRADES.csv"
    book_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BOOKS.csv"
    regime_csv = REPORTS_DIR / f"{OUTPUT_STEM}_REGIME_BY_BOOK.csv"
    filter_csv = REPORTS_DIR / f"{OUTPUT_STEM}_FILTER_TESTS.csv"
    portfolio_csv = REPORTS_DIR / f"{OUTPUT_STEM}_PORTFOLIOS.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    tagged = pd.concat(tagged_frames, ignore_index=True)
    tagged.to_csv(tagged_path, index=False)
    write_csv(book_csv, book_rows)
    write_csv(regime_csv, regime_rows)
    write_csv(filter_csv, filter_rows)
    write_csv(portfolio_csv, portfolio_rows)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {
            "regime_days": rel(REGIME_DAYS),
            **{spec["book"]: rel(spec["path"]) for spec in BOOK_SPECS},
        },
        "book_rows": book_rows,
        "regime_rows": regime_rows,
        "filter_rows": filter_rows,
        "portfolio_rows": portfolio_rows,
        "decision": decision,
        "outputs": {
            "report_md": rel(md_path),
            "report_json": rel(json_path),
            "book_csv": rel(book_csv),
            "regime_by_book_csv": rel(regime_csv),
            "filter_tests_csv": rel(filter_csv),
            "portfolio_csv": rel(portfolio_csv),
            "tagged_trades_csv": rel(tagged_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_md(payload), encoding="utf-8")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
