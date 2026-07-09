from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_10Y_REGIME_MAP_20260709"

HISTORICAL_D1 = (
    PHASE1_ROOT.parents[0]
    / "xauusd-phase0"
    / "data"
    / "processed"
    / "bars"
    / "capital_com"
    / "XAUUSD"
    / "D1"
    / "XAUUSD_capital_com_D1_20160104_20250701.csv"
)
DUKASCOPY_D1 = (
    PHASE1_ROOT.parents[0]
    / "xauusd-phase0"
    / "data"
    / "processed"
    / "bars"
    / "dukascopy"
    / "XAUUSD"
    / "D1"
    / "XAUUSD_dukascopy_D1_20160101_20250701_derived_from_m5.csv"
)
MT5_BRIDGE_D1 = (
    PHASE1_ROOT
    / "data"
    / "ml"
    / "a3_meta_v1"
    / "c02"
    / "xauusd_c02_multiacct_202607090713_gdb8b1169_c9221d066"
    / "raw"
    / "A1"
    / "bars"
    / "XAUUSD_D1.csv"
)
MT5_BRIDGE_REPORT = REPO_ROOT / "outputs" / "reports" / "C02_BAR_TICK_EXPORT_REPORT_REGIME_20260709.md"
RECENT_ROUTER_MONTHS = REPORTS_DIR / "A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_MONTHS.csv"

ANALYSIS_START = pd.Timestamp("2016-07-09", tz="UTC")
ANALYSIS_END = pd.Timestamp("2026-07-09", tz="UTC")

REGIME_ORDER = ["uptrend", "downtrend", "chop", "compression", "shock", "transition", "unknown"]


@dataclass(frozen=True)
class RegimeRule:
    name: str
    description: str


RULES = [
    RegimeRule(
        "shock",
        "ATR14 percentile >= 95 over a 252-bar window, or a very large one-day / five-day move. "
        "This isolates violent volatility bursts before trend labels.",
    ),
    RegimeRule(
        "compression",
        "ATR14 percentile <= 25 and the 20-day high-low range is in the lower 35% of its 252-bar history.",
    ),
    RegimeRule(
        "uptrend",
        "Close > EMA50 > EMA200, EMA50 rising over 20 bars, and 60-day return > +3%.",
    ),
    RegimeRule(
        "downtrend",
        "Close < EMA50 < EMA200, EMA50 falling over 20 bars, and 60-day return < -3%.",
    ),
    RegimeRule(
        "transition",
        "Directional 20-day or 60-day movement is material, but the EMA stack has not confirmed a clean trend.",
    ),
    RegimeRule(
        "chop",
        "Default state: mixed EMA structure, weak directional movement, or range movement without compression.",
    ),
]

MAJOR_EPISODE_SPECS = [
    {
        "start": "2016-07-09",
        "end": "2016-09-30",
        "label": "post-spike compression / range",
        "read": "Gold paused after the 2016 upside move; volatility contracted and direction was unreliable.",
        "specialist": "R3 compression or R4 range; avoid chasing trend continuation.",
    },
    {
        "start": "2016-10-01",
        "end": "2016-12-31",
        "label": "downtrend selloff",
        "read": "Clean downside repricing into year-end.",
        "specialist": "R2 short continuation / pullback rejection.",
    },
    {
        "start": "2017-01-01",
        "end": "2018-05-31",
        "label": "broad chop with short trend bursts",
        "read": "Range-dominant structure with intermittent upside legs that did not persist cleanly.",
        "specialist": "R4 range/reclaim first; R1 only when router confirms a clean uptrend sub-state.",
    },
    {
        "start": "2018-06-01",
        "end": "2018-09-30",
        "label": "compression into downtrend",
        "read": "Low-volatility squeeze resolved into a persistent bearish leg.",
        "specialist": "R3 compression-break followed by R2 downtrend short.",
    },
    {
        "start": "2018-10-01",
        "end": "2019-05-31",
        "label": "base-building chop",
        "read": "Gold stopped falling, but trend quality stayed mixed before the 2019 breakout.",
        "specialist": "R4 range/reversal; wait for R1 breakout confirmation.",
    },
    {
        "start": "2019-06-01",
        "end": "2020-09-30",
        "label": "major bull expansion with shock bursts",
        "read": "The first major decade bull leg; shock months appeared inside the upside trend.",
        "specialist": "R1 uptrend long, with R0 shock throttle during violent expansion.",
    },
    {
        "start": "2020-10-01",
        "end": "2021-03-31",
        "label": "post-bull correction / chop-to-downtrend",
        "read": "The 2020 bull leg cooled into range, then downside pressure.",
        "specialist": "R4 range defense first; R2 only after structural downtrend confirms.",
    },
    {
        "start": "2021-04-01",
        "end": "2022-01-31",
        "label": "compression and range rotation",
        "read": "Mostly low-volatility compression/range with false directional starts.",
        "specialist": "R3 compression and R4 failed-break specialists.",
    },
    {
        "start": "2022-02-01",
        "end": "2022-03-31",
        "label": "upside event shock",
        "read": "Fast geopolitical/inflation repricing; volatility dominated normal trend logic.",
        "specialist": "R0 event/shock handling; R1 only after volatility normalizes.",
    },
    {
        "start": "2022-04-01",
        "end": "2022-10-31",
        "label": "Fed/USD downtrend",
        "read": "Persistent bearish regime after the event spike failed.",
        "specialist": "R2 short specialist; long continuation should be routed off.",
    },
    {
        "start": "2022-11-01",
        "end": "2023-05-31",
        "label": "recovery uptrend with shock rally",
        "read": "Reversal from the 2022 lows into renewed upside trend.",
        "specialist": "R1 long after transition; R0 around shock spikes.",
    },
    {
        "start": "2023-06-01",
        "end": "2023-10-31",
        "label": "compression then violent reversal",
        "read": "Summer compression broke down, then reversed sharply in October.",
        "specialist": "R3/R4; avoid assuming downtrend continuation after extended compression breaks.",
    },
    {
        "start": "2023-11-01",
        "end": "2024-05-31",
        "label": "fresh bull breakout / high-vol uptrend",
        "read": "New upside leg with March-April acceleration.",
        "specialist": "R1 long, with shock throttle during acceleration.",
    },
    {
        "start": "2024-06-01",
        "end": "2024-12-31",
        "label": "bull trend with mid-year chop and year-end pause",
        "read": "Trend remained constructive, but entry quality depended heavily on regime routing.",
        "specialist": "R1 when clean; R4 during pauses.",
    },
    {
        "start": "2025-01-01",
        "end": "2026-02-28",
        "label": "extreme bull expansion / crowded upside",
        "read": "The strongest upside phase in the sample; this is where the long specialist harvest came from.",
        "specialist": "R1 long was the correct engine; R0 throttle needed during shock months.",
    },
    {
        "start": "2026-03-01",
        "end": "2026-07-09",
        "label": "bull break into chop/downtrend",
        "read": "The market stopped rewarding long continuation; exact-MT5 router confirms chop in Mar-May and downtrend in June.",
        "specialist": "R1 off; R2 downtrend plus R4 chop are the missing coverage.",
    },
]


def parse_utc(value: str) -> pd.Timestamp:
    return pd.to_datetime(value, utc=True)


def read_phase0_d1(path: Path, source: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["date"] = frame["time_utc"].dt.date
    frame["source"] = source
    return frame[["time_utc", "date", "open", "high", "low", "close", "source"]].copy()


def read_mt5_d1(path: Path, source: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame["date"] = frame["time_utc"].dt.date
    frame["source"] = source
    return frame[["time_utc", "date", "open", "high", "low", "close", "source"]].copy()


def load_backbone() -> pd.DataFrame:
    historical = read_phase0_d1(HISTORICAL_D1, "capital_com_processed_d1")
    mt5 = read_mt5_d1(MT5_BRIDGE_D1, "mt5_a1_c02_read_only_export")

    # Capital.com's last historical row closes the 2025-06-30 session. The MT5
    # export starts with the 2025-07-01 bar, so use the MT5 bridge from 2025-07-01.
    historical = historical[historical["time_utc"] < pd.Timestamp("2025-07-01", tz="UTC")]
    combined = pd.concat([historical, mt5], ignore_index=True)
    combined = combined[(combined["time_utc"] >= pd.Timestamp("2016-01-01", tz="UTC")) & (combined["time_utc"] <= ANALYSIS_END)]
    combined = combined.sort_values("time_utc").drop_duplicates("date", keep="last").reset_index(drop=True)
    numeric_cols = ["open", "high", "low", "close"]
    for col in numeric_cols:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")
    combined = combined.dropna(subset=numeric_cols).reset_index(drop=True)
    return combined


def percentile_rank_current(values: pd.Series) -> float:
    current = values.iloc[-1]
    if pd.isna(current):
        return np.nan
    valid = values.dropna()
    if valid.empty:
        return np.nan
    return float((valid <= current).sum() / len(valid))


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    prev_close = data["close"].shift(1)
    tr = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - prev_close).abs(),
            (data["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["atr14"] = tr.rolling(14, min_periods=10).mean()
    data["atr14_pct_252"] = data["atr14"].rolling(252, min_periods=120).apply(percentile_rank_current, raw=False) * 100.0
    data["ema20"] = data["close"].ewm(span=20, adjust=False, min_periods=20).mean()
    data["ema50"] = data["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    data["ema200"] = data["close"].ewm(span=200, adjust=False, min_periods=200).mean()
    data["ema50_slope_20_pct"] = (data["ema50"] / data["ema50"].shift(20) - 1.0) * 100.0
    data["ret1_pct"] = (data["close"] / data["close"].shift(1) - 1.0) * 100.0
    data["ret5_pct"] = (data["close"] / data["close"].shift(5) - 1.0) * 100.0
    data["ret20_pct"] = (data["close"] / data["close"].shift(20) - 1.0) * 100.0
    data["ret60_pct"] = (data["close"] / data["close"].shift(60) - 1.0) * 100.0
    data["ret120_pct"] = (data["close"] / data["close"].shift(120) - 1.0) * 100.0
    data["range1_pct"] = (data["high"] - data["low"]) / data["close"] * 100.0
    data["range20_pct"] = (data["high"].rolling(20, min_periods=15).max() - data["low"].rolling(20, min_periods=15).min()) / data["close"] * 100.0
    data["range20_pct_rank_252"] = data["range20_pct"].rolling(252, min_periods=120).apply(percentile_rank_current, raw=False) * 100.0
    return data


def classify_row(row: pd.Series) -> str:
    required = ["atr14_pct_252", "ema50", "ema200", "ema50_slope_20_pct", "ret20_pct", "ret60_pct", "range20_pct_rank_252"]
    if any(pd.isna(row.get(col)) for col in required):
        return "unknown"

    shock = (
        row["atr14_pct_252"] >= 95.0
        or abs(row["ret1_pct"]) >= 3.5
        or abs(row["ret5_pct"]) >= 7.5
        or row["range1_pct"] >= 4.0
    )
    if shock:
        return "shock"

    compression = row["atr14_pct_252"] <= 25.0 and row["range20_pct_rank_252"] <= 35.0
    if compression:
        return "compression"

    upside_breaking = row["ema50_slope_20_pct"] > 0.0 and row["close"] < row["ema20"] and row["ret20_pct"] <= -4.0
    downside_breaking = row["ema50_slope_20_pct"] < 0.0 and row["close"] > row["ema20"] and row["ret20_pct"] >= 4.0
    if upside_breaking or downside_breaking:
        return "transition"

    uptrend = (
        row["close"] > row["ema50"]
        and row["ema50"] > row["ema200"]
        and row["ema50_slope_20_pct"] > 0.0
        and row["ret60_pct"] > 3.0
    )
    if uptrend:
        return "uptrend"

    downtrend = (
        row["close"] < row["ema50"]
        and row["ema50"] < row["ema200"]
        and row["ema50_slope_20_pct"] < 0.0
        and row["ret60_pct"] < -3.0
    )
    if downtrend:
        return "downtrend"

    if abs(row["ret20_pct"]) >= 4.0 or abs(row["ret60_pct"]) >= 8.0:
        return "transition"
    return "chop"


def dominant_regime(values: pd.Series) -> tuple[str, float]:
    valid = [str(value) for value in values if str(value) != "unknown"]
    if not valid:
        return "unknown", 0.0
    counts = Counter(valid)
    regime, count = counts.most_common(1)[0]
    return regime, round(100.0 * count / len(valid), 2)


def month_rows(daily: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scoped = daily[(daily["time_utc"] >= ANALYSIS_START) & (daily["time_utc"] <= ANALYSIS_END)].copy()
    scoped["month"] = scoped["time_utc"].dt.strftime("%Y-%m")
    for month, group in scoped.groupby("month", sort=True):
        regime, share = dominant_regime(group["regime"])
        counts = group["regime"].value_counts().to_dict()
        first = group.iloc[0]
        last = group.iloc[-1]
        row: dict[str, Any] = {
            "month": month,
            "start": first["time_utc"].date().isoformat(),
            "end": last["time_utc"].date().isoformat(),
            "bars": int(len(group)),
            "dominant_regime": regime,
            "dominant_share_pct": share,
            "start_close": round(float(first["close"]), 2),
            "end_close": round(float(last["close"]), 2),
            "month_return_pct": round((float(last["close"]) / float(first["close"]) - 1.0) * 100.0, 2),
            "avg_atr14_pct_252": round(float(group["atr14_pct_252"].mean()), 2) if group["atr14_pct_252"].notna().any() else 0.0,
            "source_mix": ",".join(f"{k}:{v}" for k, v in sorted(group["source"].value_counts().to_dict().items())),
        }
        for regime_name in REGIME_ORDER:
            row[f"{regime_name}_days"] = int(counts.get(regime_name, 0))
            row[f"{regime_name}_pct"] = round(100.0 * counts.get(regime_name, 0) / len(group), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def segment_rows(monthly: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    current: list[pd.Series] = []
    for _, row in monthly.iterrows():
        if not current or row["dominant_regime"] == current[-1]["dominant_regime"]:
            current.append(row)
            continue
        rows.append(render_segment(current))
        current = [row]
    if current:
        rows.append(render_segment(current))
    return pd.DataFrame(rows)


def render_segment(rows: list[pd.Series]) -> dict[str, Any]:
    first = rows[0]
    last = rows[-1]
    months = len(rows)
    regime = str(first["dominant_regime"])
    start_close = float(first["start_close"])
    end_close = float(last["end_close"])
    returns = [float(row["month_return_pct"]) for row in rows]
    total_bars = sum(int(row["bars"]) for row in rows)
    regime_days = sum(int(row[f"{regime}_days"]) for row in rows if f"{regime}_days" in row)
    return {
        "start_month": first["month"],
        "end_month": last["month"],
        "months": months,
        "dominant_regime": regime,
        "regime_day_share_pct": round(100.0 * regime_days / total_bars, 2) if total_bars else 0.0,
        "start_close": round(start_close, 2),
        "end_close": round(end_close, 2),
        "segment_return_pct": round((end_close / start_close - 1.0) * 100.0, 2) if start_close else 0.0,
        "avg_month_return_pct": round(float(np.mean(returns)), 2) if returns else 0.0,
        "best_month_pct": round(float(np.max(returns)), 2) if returns else 0.0,
        "worst_month_pct": round(float(np.min(returns)), 2) if returns else 0.0,
    }


def compact_segments(segments: pd.DataFrame, min_months: int = 2) -> pd.DataFrame:
    # Single-month flips are useful diagnostics, but the high-level map is easier
    # to read when tiny interruptions are absorbed into neighboring regimes.
    if segments.empty:
        return segments
    expanded: list[dict[str, Any]] = []
    for _, seg in segments.iterrows():
        if int(seg["months"]) >= min_months:
            expanded.append(seg.to_dict())
        else:
            expanded.append(seg.to_dict())
    return pd.DataFrame(expanded)


def load_router_recent_months() -> pd.DataFrame:
    if not RECENT_ROUTER_MONTHS.exists():
        return pd.DataFrame()
    frame = pd.read_csv(RECENT_ROUTER_MONTHS)
    return frame[frame["period"].astype(str).str.startswith("last_6_months")].copy()


def cross_check_sources() -> dict[str, Any]:
    capital = read_phase0_d1(HISTORICAL_D1, "capital")
    dukas = read_phase0_d1(DUKASCOPY_D1, "dukascopy")
    capital = capital[(capital["time_utc"] >= ANALYSIS_START) & (capital["time_utc"] <= pd.Timestamp("2025-07-01", tz="UTC"))]
    dukas = dukas[(dukas["time_utc"] >= ANALYSIS_START) & (dukas["time_utc"] <= pd.Timestamp("2025-07-01", tz="UTC"))]
    merged = capital[["date", "close"]].merge(dukas[["date", "close"]], on="date", suffixes=("_capital", "_dukascopy"))
    merged["close_diff"] = (pd.to_numeric(merged["close_capital"]) - pd.to_numeric(merged["close_dukascopy"])).abs()
    merged["ret_capital"] = pd.to_numeric(merged["close_capital"]).pct_change()
    merged["ret_dukascopy"] = pd.to_numeric(merged["close_dukascopy"]).pct_change()
    return {
        "capital_rows": int(len(capital)),
        "dukascopy_rows": int(len(dukas)),
        "common_dates": int(len(merged)),
        "median_abs_close_diff": round(float(merged["close_diff"].median()), 4) if not merged.empty else 0.0,
        "p95_abs_close_diff": round(float(merged["close_diff"].quantile(0.95)), 4) if not merged.empty else 0.0,
        "daily_return_corr": round(float(merged[["ret_capital", "ret_dukascopy"]].corr().iloc[0, 1]), 6)
        if len(merged) > 5
        else 0.0,
    }


def regime_distribution(daily: pd.DataFrame) -> list[dict[str, Any]]:
    scoped = daily[(daily["time_utc"] >= ANALYSIS_START) & (daily["time_utc"] <= ANALYSIS_END)]
    total = len(scoped)
    counts = scoped["regime"].value_counts().to_dict()
    return [
        {
            "regime": regime,
            "days": int(counts.get(regime, 0)),
            "pct": round(100.0 * counts.get(regime, 0) / total, 2) if total else 0.0,
        }
        for regime in REGIME_ORDER
    ]


def major_episode_rows(daily: pd.DataFrame) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for spec in MAJOR_EPISODE_SPECS:
        start = pd.Timestamp(spec["start"], tz="UTC")
        end = pd.Timestamp(spec["end"], tz="UTC")
        group = daily[(daily["time_utc"] >= start) & (daily["time_utc"] <= end)].copy()
        if group.empty:
            continue
        counts = group["regime"].value_counts().to_dict()
        dominant, share = dominant_regime(group["regime"])
        first = group.iloc[0]
        last = group.iloc[-1]
        row: dict[str, Any] = {
            "start": spec["start"],
            "end": spec["end"],
            "label": spec["label"],
            "dominant_regime": dominant,
            "dominant_share_pct": share,
            "bars": int(len(group)),
            "start_close": round(float(first["close"]), 2),
            "end_close": round(float(last["close"]), 2),
            "return_pct": round((float(last["close"]) / float(first["close"]) - 1.0) * 100.0, 2),
            "read": spec["read"],
            "specialist": spec["specialist"],
        }
        for regime in REGIME_ORDER:
            row[f"{regime}_pct"] = round(100.0 * counts.get(regime, 0) / len(group), 2)
        output.append(row)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(path, index=False)
        return
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD 10-Year Regime Map",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Analysis window: `{payload['analysis_start']}` to `{payload['analysis_end']}`",
        "",
        "This is a market-regime analysis, not a strategy backtest. It uses daily OHLC bars to map regimes, "
        "then references the exact-MT5 Router V1 recent snapshot as a 2026 cross-check.",
        "",
        "## Data Sources",
        "",
        f"- Historical backbone: `{payload['inputs']['historical_d1']}`",
        f"- MT5 read-only bridge: `{payload['inputs']['mt5_bridge_d1']}`",
        f"- MT5 bridge export report: `{payload['inputs']['mt5_bridge_report']}`",
        f"- Recent exact-MT5 router months: `{payload['inputs']['recent_router_months']}`",
        "",
        "## Source Cross-Check",
        "",
        "| Check | Value |",
        "| --- | ---: |",
    ]
    for key, value in payload["source_cross_check"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Classifier Rules",
            "",
            "| Regime | Rule |",
            "| --- | --- |",
        ]
    )
    for rule in RULES:
        lines.append(f"| `{rule.name}` | {rule.description} |")

    lines.extend(
        [
            "",
            "## 10-Year Regime Distribution",
            "",
            "| Regime | Days | Share % |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in payload["regime_distribution"]:
        lines.append(f"| `{row['regime']}` | {row['days']} | {row['pct']:.2f} |")

    lines.extend(
        [
            "",
            "## Major Regime Episodes",
            "",
            "| Start | End | Episode | Dominant | Return % | Read | Specialist implication |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in payload["major_episodes"]:
        lines.append(
            f"| {row['start']} | {row['end']} | {row['label']} | `{row['dominant_regime']}` "
            f"({row['dominant_share_pct']:.2f}%) | {row['return_pct']:.2f} | {row['read']} | {row['specialist']} |"
        )

    lines.extend(
        [
            "",
            "## Detailed Monthly Segments",
            "",
            "| Start | End | Months | Regime | Regime-day share % | Return % | Best month % | Worst month % |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["segments"]:
        lines.append(
            f"| {row['start_month']} | {row['end_month']} | {row['months']} | `{row['dominant_regime']}` | "
            f"{row['regime_day_share_pct']:.2f} | {row['segment_return_pct']:.2f} | "
            f"{row['best_month_pct']:.2f} | {row['worst_month_pct']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## 2026 Exact-MT5 Router Cross-Check",
            "",
            "| Month | Router dominant | Share % | Uptrend % | Downtrend % | Chop % | Shock % | Compression % |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["router_recent_months"]:
        lines.append(
            f"| {row['month']} | `{row['dominant_regime']}` | {float(row['dominant_share_pct']):.2f} | "
            f"{float(row['uptrend_pct']):.2f} | {float(row['downtrend_pct']):.2f} | "
            f"{float(row['chop_pct']):.2f} | {float(row['shock_pct']):.2f} | "
            f"{float(row['compression_pct']):.2f} |"
        )

    lines.extend(
        [
            "",
            "## Strategy Implication",
            "",
            "- XAUUSD has not been one market. It rotated through clean bull legs, corrections/downtrends, high-volatility shocks, low-volatility compression, and long mixed chop.",
            "- A single long specialist can work in the bull/uptrend segments, but it should be expected to go quiet or lose edge in chop/downtrend/shock unless routed off.",
            "- The recent 2026 exact-MT5 snapshot is mostly chop/downtrend after January. That matches why the long edge went dormant in the last three months.",
            "- The specialist roadmap should therefore be regime-first: R1 uptrend long, R2 downtrend short, R3 compression breakout, R4 chop/range fade, and R0 shock no-trade/event handling.",
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
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    daily = add_indicators(load_backbone())
    daily["regime"] = daily.apply(classify_row, axis=1)
    daily_scoped = daily[(daily["time_utc"] >= ANALYSIS_START) & (daily["time_utc"] <= ANALYSIS_END)].copy()
    daily_scoped["date"] = daily_scoped["time_utc"].dt.date.astype(str)

    monthly = month_rows(daily)
    segments = segment_rows(monthly)
    # Assign stable IDs after segment construction.
    segments.insert(0, "segment_id", range(1, len(segments) + 1))

    router_recent = load_router_recent_months()
    daily_path = REPORTS_DIR / f"{OUTPUT_STEM}_DAYS.csv"
    monthly_path = REPORTS_DIR / f"{OUTPUT_STEM}_MONTHS.csv"
    segments_path = REPORTS_DIR / f"{OUTPUT_STEM}_SEGMENTS.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    daily_cols = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "source",
        "regime",
        "atr14",
        "atr14_pct_252",
        "ema50",
        "ema200",
        "ema50_slope_20_pct",
        "ret20_pct",
        "ret60_pct",
        "range20_pct_rank_252",
    ]
    write_csv(daily_path, daily_scoped[daily_cols])
    write_csv(monthly_path, monthly)
    write_csv(segments_path, segments)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "analysis_start": ANALYSIS_START.date().isoformat(),
        "analysis_end": ANALYSIS_END.date().isoformat(),
        "inputs": {
            "historical_d1": str(HISTORICAL_D1),
            "dukascopy_d1_comparison": str(DUKASCOPY_D1),
            "mt5_bridge_d1": str(MT5_BRIDGE_D1),
            "mt5_bridge_report": str(MT5_BRIDGE_REPORT),
            "recent_router_months": str(RECENT_ROUTER_MONTHS),
        },
        "rules": [rule.__dict__ for rule in RULES],
        "source_cross_check": cross_check_sources(),
        "regime_distribution": regime_distribution(daily),
        "major_episodes": major_episode_rows(daily),
        "segments": segments.to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
        "router_recent_months": router_recent.to_dict(orient="records"),
        "outputs": {
            "report_md": str(md_path),
            "report_json": str(json_path),
            "daily_csv": str(daily_path),
            "monthly_csv": str(monthly_path),
            "segments_csv": str(segments_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
