from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
MT5_REPORTS = REPORTS / "mt5_backtests"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_PREREG_2026_07_05.md"
REFERENCE_ETF = REPO_ROOT / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "etf"
REFERENCE_FUTURES = REPO_ROOT / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "futures"
RECENT_ETF = REPO_ROOT / "forex-research" / "data" / "external" / "yahoo_etf"

DESIGN_FROM = "2016.01.01"
DESIGN_TO = "2021.12.31"
EXAM_FROM = "2022.07.01"
EXAM_TO = "2026.06.30"


@dataclass(frozen=True)
class Family:
    family_id: str
    label: str
    design_trade_csv: Path
    exam_trade_csv: Path


def families() -> list[Family]:
    rr2_design = MT5_REPORTS / "a1_momentum_variants_owner_goal_rr2_profit_lock_design_201601_202112_20260701"
    rr2_exam = MT5_REPORTS / "a1_momentum_variants_owner_goal_rr2_profit_lock_exam_202207_202606_20260701"
    or_design = MT5_REPORTS / "a1_momentum_variants_owner_goal_orrev_step4_design_201601_202112_20260701"
    or_exam = MT5_REPORTS / "a1_momentum_variants_owner_goal_orrev_step4_exam_202207_202606_20260701"
    rr2_long_exam = (
        MT5_REPORTS
        / "a1_momentum_variants_four_year_rr2_long_only_2022_07_2026_06_momentum_usd_20260701"
        / "A1XauM5Momentum_FOUR_YEAR_RR2_LONG_ONLY_2022_07_2026_06_MOMENTUM_USD_XAUUSD_M5_rr_2p0_long_only_h1_h4_atr15_no0910_trades.csv"
    )
    return [
        Family(
            "rr2_baseline_no_lock",
            "RR2 long-only baseline, no profit lock",
            rr2_design
            / "A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_DESIGN_201601_202112_XAUUSD_M5_rr2_baseline_no_lock_trades.csv",
            rr2_long_exam,
        ),
        Family(
            "rr2_lock100_010",
            "RR2 profit lock trigger 1.00R, lock 0.10R",
            rr2_design
            / "A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_DESIGN_201601_202112_XAUUSD_M5_rr2_lock100_010_trades.csv",
            rr2_exam
            / "A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_EXAM_202207_202606_XAUUSD_M5_rr2_lock100_010_trades.csv",
        ),
        Family(
            "rr2_lock080_010",
            "RR2 profit lock trigger 0.80R, lock 0.10R",
            rr2_design
            / "A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_DESIGN_201601_202112_XAUUSD_M5_rr2_lock080_010_trades.csv",
            rr2_exam
            / "A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_EXAM_202207_202606_XAUUSD_M5_rr2_lock080_010_trades.csv",
        ),
        Family(
            "orrev_london_firm_stop15",
            "Opening-range reversal London firm stop15",
            or_design
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_DESIGN_201601_202112_XAUUSD_M5_orrev_london_firm_stop15_trades.csv",
            or_exam
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_EXAM_202207_202606_XAUUSD_M5_orrev_london_firm_stop15_trades.csv",
        ),
        Family(
            "orrev_london_firm_stop10",
            "Opening-range reversal London firm stop10",
            or_design
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_DESIGN_201601_202112_XAUUSD_M5_orrev_london_firm_stop10_trades.csv",
            or_exam
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_EXAM_202207_202606_XAUUSD_M5_orrev_london_firm_stop10_trades.csv",
        ),
        Family(
            "orrev_london_loose_stop15",
            "Opening-range reversal London loose stop15",
            or_design
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_DESIGN_201601_202112_XAUUSD_M5_orrev_london_loose_stop15_trades.csv",
            or_exam
            / "A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_EXAM_202207_202606_XAUUSD_M5_orrev_london_loose_stop15_trades.csv",
        ),
    ]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_file(root: Path, pattern: str) -> Path:
    files = sorted(root.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing {pattern} under {root}")
    return files[-1]


def read_csv_frames(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        require_file(path)
        frame = pd.read_csv(path)
        frame["_source_file"] = str(path)
        frames.append(frame)
    merged = pd.concat(frames, ignore_index=True)
    merged["date_utc"] = pd.to_datetime(merged["date_utc"], utc=True, errors="coerce").dt.date
    merged = merged.dropna(subset=["date_utc"]).sort_values(["date_utc", "_source_file"])
    return merged.drop_duplicates(subset=["date_utc"], keep="last").reset_index(drop=True)


def single_context(name: str, paths: list[Path], close_col: str) -> tuple[pd.DataFrame, dict[str, str]]:
    frame = read_csv_frames(paths)
    values = pd.to_numeric(frame[close_col], errors="coerce")
    ctx = pd.DataFrame({"observation_date": frame["date_utc"], f"{name}_close": values}).dropna()
    ctx = ctx[ctx[f"{name}_close"] > 0].sort_values("observation_date").reset_index(drop=True)
    ctx[f"{name}_5d_pct"] = ctx[f"{name}_close"].pct_change(5) * 100.0
    ctx[f"{name}_20d_pct"] = ctx[f"{name}_close"].pct_change(20) * 100.0
    return ctx, {f"{name}_{idx}": str(path) for idx, path in enumerate(paths, start=1)}


def ratio_context(
    name: str,
    paths: list[Path],
    left_col: str,
    right_col: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
    frame = read_csv_frames(paths)
    left = pd.to_numeric(frame[left_col], errors="coerce")
    right = pd.to_numeric(frame[right_col], errors="coerce")
    ctx = pd.DataFrame({"observation_date": frame["date_utc"], f"{name}_left": left, f"{name}_right": right}).dropna()
    ctx = ctx[(ctx[f"{name}_left"] > 0) & (ctx[f"{name}_right"] > 0)].sort_values("observation_date").reset_index(drop=True)
    ctx[f"{name}_ratio"] = ctx[f"{name}_left"] / ctx[f"{name}_right"]
    ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
    ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
    return ctx[["observation_date", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]], {
        f"{name}_{idx}": str(path) for idx, path in enumerate(paths, start=1)
    }


def build_macro_context() -> tuple[pd.DataFrame, dict[str, str]]:
    pieces: list[pd.DataFrame] = []
    sources: dict[str, str] = {}

    specs = [
        single_context(
            "gld",
            [
                REFERENCE_ETF / "gld_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "haven_liquidity", "gld_daily_yahoo_*.csv"),
            ],
            "close",
        ),
        ratio_context(
            "gdx_gld",
            [
                REFERENCE_ETF / "gdx_gld_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "haven_liquidity", "gdx_gld_daily_yahoo_*.csv"),
            ],
            "gdx_close",
            "gld_close",
        ),
        ratio_context(
            "spy_tlt",
            [
                REFERENCE_ETF / "spy_tlt_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "haven_liquidity", "spy_tlt_daily_yahoo_*.csv"),
            ],
            "spy_close",
            "tlt_close",
        ),
        ratio_context(
            "tlt_uup",
            [
                REFERENCE_ETF / "tlt_uup_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "rates_dollar", "tlt_uup_daily_yahoo_*.csv"),
            ],
            "tlt_close",
            "uup_close",
        ),
        ratio_context(
            "tlt_shy",
            [
                REFERENCE_ETF / "tlt_shy_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "rates_dollar", "tlt_shy_daily_yahoo_*.csv"),
            ],
            "tlt_close",
            "shy_close",
        ),
        ratio_context(
            "uso_uup",
            [
                REFERENCE_ETF / "uso_uup_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "real_asset_rotation", "uso_uup_daily_yahoo_*.csv"),
            ],
            "uso_close",
            "uup_close",
        ),
        ratio_context(
            "hg_gc",
            [
                REFERENCE_FUTURES / "hg_gc_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "real_asset_rotation", "hg_gc_daily_yahoo_*.csv"),
            ],
            "hg_close",
            "gc_close",
        ),
        ratio_context(
            "slv_gld",
            [
                REFERENCE_ETF / "slv_gld_daily_yahoo_2015_2025.csv",
                latest_file(RECENT_ETF / "real_asset_rotation", "slv_gld_daily_yahoo_*.csv"),
            ],
            "slv_close",
            "gld_close",
        ),
    ]
    for frame, frame_sources in specs:
        pieces.append(frame)
        sources.update(frame_sources)

    context = pieces[0]
    for piece in pieces[1:]:
        context = context.merge(piece, on="observation_date", how="outer")
    context = context.sort_values("observation_date").ffill().dropna().reset_index(drop=True)
    context["real_asset_reflation_score"] = (
        context["uso_uup_20d_pct"] / 6.0 + context["hg_gc_20d_pct"] / 3.0 + context["slv_gld_20d_pct"] / 3.0
    )
    context["haven_liquidity_score"] = (
        context["gld_20d_pct"] / 4.0 + context["gdx_gld_20d_pct"] / 5.0 - context["spy_tlt_20d_pct"] / 5.0
    )
    context["rates_dollar_score"] = context["tlt_uup_20d_pct"] / 3.0 + context["tlt_shy_20d_pct"] / 3.0
    context["available_from_date"] = context["observation_date"].map(lambda value: value + timedelta(days=1))
    return context, sources


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def read_trades(path: Path) -> pd.DataFrame:
    require_file(path)
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["profit_float"] = frame["profit_aed"].map(lambda value: parse_money(str(value)))
    frame["entry_date_obj"] = pd.to_datetime(frame["entry_date"], errors="coerce").dt.date
    frame["entry_time_obj"] = pd.to_datetime(frame["entry_time"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    frame["direction_norm"] = frame["direction"].astype(str).str.upper()
    return frame.dropna(subset=["entry_date_obj", "entry_time_obj"]).sort_values("entry_time_obj").reset_index(drop=True)


def attach_macro(trades: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    left = trades.copy()
    left["macro_asof_date"] = left["entry_date_obj"].map(lambda value: value - timedelta(days=1))
    left["macro_asof_ts"] = pd.to_datetime(left["macro_asof_date"])
    right = macro.copy()
    right["observation_ts"] = pd.to_datetime(right["observation_date"])
    return pd.merge_asof(
        left.sort_values("macro_asof_ts"),
        right.sort_values("observation_ts"),
        left_on="macro_asof_ts",
        right_on="observation_ts",
        direction="backward",
    ).sort_values("entry_time_obj").reset_index(drop=True)


def mt5_date(value: str) -> date:
    return datetime.strptime(value, "%Y.%m.%d").date()


def trading_weekday_count(start: date, end: date) -> int:
    count = 0
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5:
            count += 1
        cursor += timedelta(days=1)
    return count


def max_closed_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def owner_metrics(frame: pd.DataFrame, from_date: str, to_date: str) -> dict[str, Any]:
    start = mt5_date(from_date)
    end = mt5_date(to_date)
    if frame.empty:
        profits: list[float] = []
    else:
        profits = [float(value) for value in frame["profit_float"].tolist()]
    wins = [value for value in profits if value > 0]
    losses = [-value for value in profits if value < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    wl_ratio = avg_win / avg_loss if avg_loss else None
    active_dates = set(frame["entry_date_obj"].tolist()) if not frame.empty else set()
    weekdays = trading_weekday_count(start, end)
    active_pct = len(active_dates) / weekdays * 100.0 if weekdays else 0.0
    sorted_pnl = sorted(profits, reverse=True)
    return {
        "trades": len(profits),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(profits) * 100.0) if profits else 0.0, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_win_loss_ratio": round(wl_ratio, 4) if wl_ratio is not None else None,
        "manual_pnl": round(sum(profits), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "active_days": len(active_dates),
        "market_weekdays": weekdays,
        "active_day_pct": round(active_pct, 2),
        "max_closed_dd": round(max_closed_drawdown(profits), 2),
        "top10_removed": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "owner_core_shape_pass": bool(profits and len(wins) / len(profits) * 100.0 >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0),
        "owner_daily_frequency_pass": active_pct >= 90.0,
    }


def last12_metrics(frame: pd.DataFrame, to_date: str) -> dict[str, Any]:
    end = mt5_date(to_date)
    start = date(end.year - 1, end.month, end.day)
    subset = frame[frame["entry_date_obj"] >= start] if not frame.empty else frame
    return owner_metrics(subset, start.strftime("%Y.%m.%d"), to_date)


def directional(frame: pd.DataFrame, column: str, positive_for_long: bool = True) -> pd.Series:
    direction = frame["direction_norm"]
    values = pd.to_numeric(frame[column], errors="coerce")
    if positive_for_long:
        return ((direction == "LONG") & (values > 0)) | ((direction == "SHORT") & (values < 0))
    return ((direction == "LONG") & (values < 0)) | ((direction == "SHORT") & (values > 0))


def traffic_score(frame: pd.DataFrame) -> pd.Series:
    direction = frame["direction_norm"]
    long_score = (
        (pd.to_numeric(frame["gld_20d_pct"], errors="coerce") > 0).astype(int)
        + (pd.to_numeric(frame["gdx_gld_20d_pct"], errors="coerce") > 0).astype(int)
        + (pd.to_numeric(frame["tlt_uup_20d_pct"], errors="coerce") > 0).astype(int)
        + (pd.to_numeric(frame["tlt_shy_20d_pct"], errors="coerce") > 0).astype(int)
    )
    short_score = (
        (pd.to_numeric(frame["gld_20d_pct"], errors="coerce") < 0).astype(int)
        + (pd.to_numeric(frame["gdx_gld_20d_pct"], errors="coerce") < 0).astype(int)
        + (pd.to_numeric(frame["tlt_uup_20d_pct"], errors="coerce") < 0).astype(int)
        + (pd.to_numeric(frame["tlt_shy_20d_pct"], errors="coerce") < 0).astype(int)
    )
    return long_score.where(direction == "LONG", short_score)


GateFn = Callable[[pd.DataFrame], pd.Series]


def gate_functions() -> dict[str, GateFn]:
    return {
        "all_trades": lambda frame: pd.Series(True, index=frame.index),
        "gold20_directional": lambda frame: directional(frame, "gld_20d_pct"),
        "gold5_directional": lambda frame: directional(frame, "gld_5d_pct"),
        "miners20_directional": lambda frame: directional(frame, "gdx_gld_20d_pct"),
        "rates20_directional": lambda frame: directional(frame, "rates_dollar_score"),
        "real_asset20_directional": lambda frame: directional(frame, "real_asset_reflation_score"),
        "haven20_directional": lambda frame: directional(frame, "haven_liquidity_score"),
        "traffic_green_3of4": lambda frame: traffic_score(frame) >= 3,
        "traffic_green_or_amber_2of4": lambda frame: traffic_score(frame) >= 2,
        "gold_and_rates": lambda frame: directional(frame, "gld_20d_pct") & directional(frame, "rates_dollar_score"),
        "gold_and_miners": lambda frame: directional(frame, "gld_20d_pct") & directional(frame, "gdx_gld_20d_pct"),
        "gold_rates_miners": lambda frame: directional(frame, "gld_20d_pct")
        & directional(frame, "rates_dollar_score")
        & directional(frame, "gdx_gld_20d_pct"),
    }


def rank_tuple(row: dict[str, Any]) -> tuple[float, ...]:
    metrics = row["metrics"]
    wr = float(metrics["win_rate_pct"])
    wl = float(metrics["avg_win_loss_ratio"] or 0.0)
    active = float(metrics["active_day_pct"])
    pf = float(metrics["profit_factor"] or 0.0)
    pnl = float(metrics["manual_pnl"])
    core = 1.0 if wr >= 50.0 and wl >= 2.0 else 0.0
    near = 1.0 if wr >= 48.0 and wl >= 1.9 else 0.0
    return (core, near, min(wr, 70.0), min(wl, 4.0) * 10.0, min(active, 100.0), pf, pnl)


def evaluate_family(stage: str, family: Family, trade_csv: Path, from_date: str, to_date: str, macro: pd.DataFrame) -> list[dict[str, Any]]:
    trades = attach_macro(read_trades(trade_csv), macro)
    results: list[dict[str, Any]] = []
    for gate_id, gate_fn in gate_functions().items():
        mask = gate_fn(trades).fillna(False) if not trades.empty else pd.Series(False, index=trades.index)
        kept = trades[mask].copy()
        metrics = owner_metrics(kept, from_date, to_date)
        results.append(
            {
                "stage": stage,
                "family_id": family.family_id,
                "family_label": family.label,
                "gate_id": gate_id,
                "trade_csv": str(trade_csv),
                "input_trades": int(len(trades)),
                "kept_trades": int(len(kept)),
                "metrics": metrics,
                "last12_metrics": last12_metrics(kept, to_date),
            }
        )
    return results


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        flat = {key: value for key, value in row.items() if key not in {"metrics", "last12_metrics"}}
        for prefix in ("metrics", "last12_metrics"):
            for key, value in row[prefix].items():
                flat[f"{prefix}_{key}"] = value
        flattened.append(flat)
    fields = sorted({key for row in flattened for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flattened)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 External Macro Traffic-Light Gate Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: diagnostic over exact MT5 trade CSVs only. No terminal, chart, preset, order, position, or broker runtime was touched.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['preregistration']}`",
        f"- Design window: `{DESIGN_FROM}` to `{DESIGN_TO}`",
        f"- Exam window: `{EXAM_FROM}` to `{EXAM_TO}`",
        f"- Gate count: `{len(payload['gate_ids'])}`",
        f"- Family count: `{len(payload['families'])}`",
        f"- Lag rule: `{payload['macro_context']['lag_rule']}`",
        "",
        "## Frozen Exam Rows",
        "",
        "| Family | Gate | Trades | WR% | W/L | Active% | PF | Manual P&L | Last12 WR/WL | Decision |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["frozen_exam_rows"]:
        metrics = row["metrics"]
        last12 = row["last12_metrics"]
        decision = (
            "OWNER_GOAL"
            if metrics["owner_core_shape_pass"] and metrics["owner_daily_frequency_pass"]
            else "CORE_SHAPE_FREQ_GAP"
            if metrics["owner_core_shape_pass"]
            else "NEAR"
            if metrics["win_rate_pct"] >= 48.0 and (metrics["avg_win_loss_ratio"] or 0.0) >= 1.9
            else "FAIL"
        )
        lines.append(
            f"| `{row['family_id']}` | `{row['gate_id']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | `{decision}` |"
        )
    lines.extend(["", "## Best Design Rows Per Family", ""])
    lines.extend(
        [
            "| Family | Gate | Trades | WR% | W/L | Active% | PF | Manual P&L |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["best_design_rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| `{row['family_id']}` | `{row['gate_id']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            payload["verdict"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['artifacts']['json']}`",
            f"- CSV: `{payload['artifacts']['csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    require_file(PREREG)
    macro, sources = build_macro_context()
    all_design: list[dict[str, Any]] = []
    all_exam: list[dict[str, Any]] = []
    family_payload: list[dict[str, Any]] = []
    for family in families():
        require_file(family.design_trade_csv)
        require_file(family.exam_trade_csv)
        family_payload.append(
            {
                "family_id": family.family_id,
                "label": family.label,
                "design_trade_csv": str(family.design_trade_csv),
                "exam_trade_csv": str(family.exam_trade_csv),
                "design_sha256": sha256_file(family.design_trade_csv),
                "exam_sha256": sha256_file(family.exam_trade_csv),
            }
        )
        all_design.extend(evaluate_family("design", family, family.design_trade_csv, DESIGN_FROM, DESIGN_TO, macro))
        all_exam.extend(evaluate_family("exam", family, family.exam_trade_csv, EXAM_FROM, EXAM_TO, macro))

    best_design_rows: list[dict[str, Any]] = []
    frozen_exam_rows: list[dict[str, Any]] = []
    for family in families():
        design_rows = [row for row in all_design if row["family_id"] == family.family_id]
        non_baseline = [row for row in design_rows if row["gate_id"] != "all_trades"]
        selected_design = sorted(non_baseline, key=rank_tuple, reverse=True)[:2]
        baseline_design = [row for row in design_rows if row["gate_id"] == "all_trades"]
        best_design_rows.extend(selected_design[:1])
        selected_gate_ids = {row["gate_id"] for row in selected_design}
        selected_gate_ids.update(row["gate_id"] for row in baseline_design)
        frozen_exam_rows.extend(
            row for row in all_exam if row["family_id"] == family.family_id and row["gate_id"] in selected_gate_ids
        )

    frozen_exam_rows = sorted(frozen_exam_rows, key=rank_tuple, reverse=True)
    core_hits = [row for row in frozen_exam_rows if row["metrics"]["owner_core_shape_pass"]]
    full_hits = [row for row in core_hits if row["metrics"]["owner_daily_frequency_pass"]]
    if full_hits:
        status = "OWNER_GOAL_HIT_REVIEW_REQUIRED"
        verdict = "An exam row reached both core shape and daily frequency. Spend the reviewer token only after packaging source hashes and full ledgers."
    elif core_hits:
        status = "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_BEFORE_REVIEW"
        verdict = "At least one exam row reached WR >= 50% and W/L >= 2.0, but daily frequency failed. Treat as a clue requiring packaging, not demo-ready."
    else:
        status = "REJECT_NO_EXTERNAL_MACRO_GATE_OWNER_SHAPE"
        verdict = "No frozen exam row reached the owner core shape. Do not spend the reviewer token on this macro-gate pass."

    report_md = REPORTS / "A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_DIAGNOSTIC_2026_07_05.md"
    report_json = report_md.with_suffix(".json")
    report_csv = REPORTS / "A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_DIAGNOSTIC_2026_07_05.csv"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "verdict": verdict,
        "preregistration": str(PREREG),
        "gate_ids": list(gate_functions().keys()),
        "families": family_payload,
        "macro_context": {
            "rows": int(len(macro)),
            "start_observation_date": str(macro["observation_date"].min()),
            "end_observation_date": str(macro["observation_date"].max()),
            "lag_rule": "For entry date D, only external observations with date_utc <= D - 1 are visible.",
            "sources": sources,
        },
        "best_design_rows": sorted(best_design_rows, key=rank_tuple, reverse=True),
        "frozen_exam_rows": frozen_exam_rows,
        "all_design_rows": sorted(all_design, key=rank_tuple, reverse=True),
        "all_exam_rows": sorted(all_exam, key=rank_tuple, reverse=True),
        "artifacts": {"markdown": str(report_md), "json": str(report_json), "csv": str(report_csv)},
        "review_spend_rule": "No reviewer unless an exam row reaches WR >= 50% and realized W/L >= 2.0.",
        "runtime_boundary": "CSV diagnostic only; no MT5 terminal invocation.",
    }
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(report_csv, payload["all_design_rows"] + payload["all_exam_rows"])
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_md), "csv": str(report_csv)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
