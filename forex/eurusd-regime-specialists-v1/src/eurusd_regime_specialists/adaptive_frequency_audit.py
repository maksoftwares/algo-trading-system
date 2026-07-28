from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config
from .research import PACKAGE_ROOT, is_quarantined, load_inputs, serialize


FAMILY = "EURUSD_ADAPTIVE_FREQUENCY_FALLBACK_AUDIT_V1"
REPO_ROOT = PACKAGE_ROOT.parents[1]
FALLBACK_ROOT = (
    REPO_ROOT
    / "eur-usd"
    / "eurusd-fast-research"
    / "regime-specialists-v2"
)
FALLBACK_OUTPUT = FALLBACK_ROOT / "outputs" / "frequency_v2_mt5"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "adaptive_frequency_fallback_audit"
REPORT_PATH = (
    PACKAGE_ROOT
    / "EURUSD_ADAPTIVE_FREQUENCY_FALLBACK_AUDIT_2026_07_28.md"
)
M15_SLEEVE = "M15_RSI_LONG_H4_TREND_OVERLAY"
CONTROL_SLEEVE = "H1_CHOP_ASIA_LONDON_SHORT_CONTROL"
COMMON_START = pd.Timestamp("2024-07-01T00:00:00Z")
COMMON_END = pd.Timestamp("2026-06-30T23:59:59Z")
EURUSD_USD_PER_PIP_AT_0P01_LOT = 0.10


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="raise")


def read_mt5_trades(
    path: Path,
    sleeve: str,
    side: str,
) -> pd.DataFrame:
    """Reconstruct trades directly from a raw MT5 Strategy Tester report."""
    raw = pd.read_html(path, encoding="utf-16")[1]
    deals_header = raw.index[raw.iloc[:, 0].astype(str).eq("Deals")]
    if len(deals_header) != 1:
        raise RuntimeError(f"Cannot locate MT5 deals table in {path}")
    deals = raw.iloc[deals_header[0] + 2 :].copy()
    deals.columns = [
        "time",
        "deal",
        "symbol",
        "type",
        "direction",
        "volume",
        "price",
        "order",
        "commission",
        "swap",
        "profit",
        "balance",
        "comment",
    ]
    deals = deals[deals["symbol"].eq("EURUSD")].copy()
    deals["time"] = pd.to_datetime(
        deals["time"], format="%Y.%m.%d %H:%M:%S"
    )
    for field in (
        "volume",
        "price",
        "commission",
        "swap",
        "profit",
    ):
        deals[field] = _numeric(deals[field])
    entries = deals[deals["direction"].eq("in")].reset_index(drop=True)
    exits = deals[deals["direction"].eq("out")].reset_index(drop=True)
    if len(entries) != len(exits):
        raise RuntimeError(f"Unpaired MT5 deals in {path}")
    if (exits["time"] < entries["time"]).any():
        raise RuntimeError(f"Exit precedes entry in {path}")
    frame = pd.DataFrame(
        {
            "entry_time": entries["time"],
            "exit_time": exits["time"],
            "sleeve": sleeve,
            "side": side,
            "volume": entries["volume"],
            "entry_price": entries["price"],
            "exit_price": exits["price"],
            "commission": exits["commission"],
            "swap": exits["swap"],
            "profit": exits["profit"],
            "net_pnl_usd": (
                exits["commission"] + exits["swap"] + exits["profit"]
            ),
            "exit_comment": exits["comment"],
        }
    )
    for column in ("entry_time", "exit_time"):
        frame[column] = (
            frame[column].dt.tz_localize("UTC").dt.as_unit("ns")
        )
    return frame


def reconstruct_portfolio() -> pd.DataFrame:
    m15 = read_mt5_trades(
        FALLBACK_OUTPUT / "M15_TREND_OVERLAY_REPORT.htm",
        M15_SLEEVE,
        "LONG",
    )
    control = read_mt5_trades(
        FALLBACK_OUTPUT / "CHOP_CONTROL_REPORT.htm",
        CONTROL_SLEEVE,
        "SHORT",
    )
    return (
        pd.concat([m15, control], ignore_index=True)
        .sort_values(["exit_time", "sleeve"])
        .reset_index(drop=True)
    )


def verify_packaged_ledger(reconstructed: pd.DataFrame) -> dict[str, Any]:
    path = FALLBACK_OUTPUT / "PORTFOLIO_TRADES.csv"
    packaged = pd.read_csv(path)
    for column in ("entry_time", "exit_time"):
        packaged[column] = (
            pd.to_datetime(packaged[column])
            .dt.tz_localize("UTC")
            .dt.as_unit("ns")
        )
    compare_columns = [
        "entry_time",
        "exit_time",
        "sleeve",
        "volume",
        "entry_price",
        "exit_price",
        "net_pnl_usd",
    ]
    left = reconstructed[compare_columns].reset_index(drop=True)
    right = packaged[compare_columns].reset_index(drop=True)
    exact_columns = ("entry_time", "exit_time", "sleeve")
    exact_match = len(left) == len(right) and all(
        left[column].equals(right[column]) for column in exact_columns
    )
    numeric_columns = (
        "volume",
        "entry_price",
        "exit_price",
        "net_pnl_usd",
    )
    numeric_match = len(left) == len(right) and all(
        np.allclose(left[column], right[column], rtol=0.0, atol=1e-12)
        for column in numeric_columns
    )
    return {
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sha256": sha256_file(path),
        "rows": int(len(packaged)),
        "raw_report_reconstruction_exact_match": bool(
            exact_match and numeric_match
        ),
    }


def report_drawdown(path: Path) -> dict[str, float]:
    table = pd.read_html(path, encoding="utf-16")[0]
    for _, row in table.iterrows():
        values = [str(value) for value in row.tolist()]
        if "Balance Drawdown Maximal:" not in values:
            continue
        matches = []
        for value in values:
            found = re.fullmatch(
                r"\s*([0-9]+(?:\.[0-9]+)?)\s+\(([0-9]+(?:\.[0-9]+)?)%\)\s*",
                value,
            )
            if found:
                pair = (float(found.group(1)), float(found.group(2)))
                if not matches or pair != matches[-1]:
                    matches.append(pair)
        if len(matches) >= 2:
            return {
                "maximum_balance_drawdown_usd": matches[0][0],
                "maximum_balance_drawdown_pct": matches[0][1] / 100.0,
                "maximum_equity_drawdown_usd": matches[1][0],
                "maximum_equity_drawdown_pct": matches[1][1] / 100.0,
            }
    raise RuntimeError(f"Cannot parse drawdown statistics from {path}")


def source_evidence() -> dict[str, Any]:
    verdict_path = FALLBACK_OUTPUT / "VERDICT.json"
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    declared = verdict["source_evidence"]
    m15_source = (
        REPO_ROOT
        / "forex-research"
        / "mt5"
        / "Experts"
        / "ForexMeanReversionScout.mq5"
    )
    m15_ex5 = FALLBACK_ROOT / "mt5" / "Experts" / "ForexMeanReversionScout.ex5"
    checks = {
        "m15_report_sha256": sha256_file(
            FALLBACK_OUTPUT / "M15_TREND_OVERLAY_REPORT.htm"
        ),
        "control_report_sha256": sha256_file(
            FALLBACK_OUTPUT / "CHOP_CONTROL_REPORT.htm"
        ),
        "m15_source_sha256": sha256_file(m15_source),
        "m15_ex5_sha256": sha256_file(m15_ex5),
    }
    compile_bytes = (
        FALLBACK_ROOT / "mt5" / "frequency_v2_m15_compile.log"
    ).read_bytes()
    compile_log = (
        compile_bytes.decode("utf-16")
        if compile_bytes.startswith((b"\xff\xfe", b"\xfe\xff"))
        or b"\x00" in compile_bytes[:100]
        else compile_bytes.decode("utf-8", errors="replace")
    )
    return {
        "declared_hashes_match": bool(
            all(checks[name] == declared[name] for name in checks)
        ),
        "hashes": checks,
        "compile_log_reports_zero_errors_zero_warnings": (
            "Result: 0 errors, 0 warnings" in compile_log
        ),
        "source_ex5_parity_status": (
            "PARTIAL_PROVENANCE_ONLY: source and EX5 hashes are recorded and "
            "the compile log is clean, but the scratch compile log does not "
            "bind its input source hash to the packaged EX5 hash."
        ),
    }


def price_time_offset_audit(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    offsets: range = range(-4, 5),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for sleeve, sleeve_trades in trades.groupby("sleeve"):
        for offset in offsets:
            utc_times = (
                sleeve_trades["entry_time"]
                - pd.Timedelta(hours=offset)
            )
            positions = m5.index.get_indexer(utc_times)
            available = positions >= 0
            reference = np.full(len(sleeve_trades), np.nan)
            is_long = sleeve_trades["side"].eq("LONG").to_numpy()
            long_mask = available & is_long
            short_mask = available & ~is_long
            reference[long_mask] = m5.iloc[
                positions[long_mask]
            ]["ask_open"].to_numpy()
            reference[short_mask] = m5.iloc[
                positions[short_mask]
            ]["bid_open"].to_numpy()
            difference = (
                np.abs(
                    sleeve_trades["entry_price"].to_numpy() - reference
                )
                / 0.0001
            )
            finite = difference[np.isfinite(difference)]
            rows.append(
                {
                    "sleeve": sleeve,
                    "broker_utc_offset_hours": offset,
                    "matched_entries": int(len(finite)),
                    "median_absolute_price_difference_pips": (
                        float(np.median(finite))
                        if len(finite)
                        else None
                    ),
                    "p90_absolute_price_difference_pips": (
                        float(np.percentile(finite, 90))
                        if len(finite)
                        else None
                    ),
                }
            )
    return pd.DataFrame(rows)


def selected_time_offset(offsets: pd.DataFrame) -> dict[str, Any]:
    best = (
        offsets.sort_values(
            [
                "sleeve",
                "median_absolute_price_difference_pips",
                "broker_utc_offset_hours",
            ]
        )
        .groupby("sleeve", as_index=False)
        .first()
    )
    selected = sorted(best["broker_utc_offset_hours"].unique().tolist())
    if selected != [0]:
        raise RuntimeError(
            f"MT5 broker time does not resolve uniquely to UTC: {selected}"
        )
    return {
        "selected_broker_utc_offset_hours": 0,
        "independent_price_alignment": best.to_dict(orient="records"),
        "interpretation": (
            "UTC is the unique minimum-median-error alignment for both "
            "sleeves against the independent Dukascopy bid/ask M5 cache."
        ),
    }


def attach_causal_regime(
    trades: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    joined = trades.copy()
    joined["state_time_utc"] = (
        joined["entry_time"].dt.floor("h") - pd.Timedelta(hours=1)
    ).dt.as_unit("ns")
    state_columns = [
        "direction",
        "phase",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        joined.sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    joined["causal_regime"] = "MISSING_CONTEXT"
    valid = joined["direction"].notna()
    shock = valid & joined["shock"].astype("boolean").fillna(False)
    joined.loc[shock, "causal_regime"] = "SHOCK"
    nonshock = valid & ~joined["shock"].astype("boolean").fillna(True)
    compression = (
        nonshock
        & joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined.loc[compression, "causal_regime"] = "JOINT_COMPRESSION"
    remaining = nonshock & ~compression
    for direction, regime in (
        ("USD_DOWN", "USD_DOWN"),
        ("NEUTRAL", "NEUTRAL"),
        ("USD_UP", "USD_UP"),
    ):
        joined.loc[
            remaining & joined["direction"].eq(direction),
            "causal_regime",
        ] = regime
    joined["quarantined"] = joined["entry_time"].map(
        lambda value: is_quarantined(
            value, "EURUSD", cfg["quarantine"]
        )
    )
    return joined.sort_values(["exit_time", "sleeve"]).reset_index(drop=True)


def profit_metrics(
    frame: pd.DataFrame,
    pnl_column: str = "net_pnl_usd",
) -> dict[str, Any]:
    values = frame[pnl_column].to_numpy(dtype=float)
    if len(values) == 0:
        return {
            "trades": 0,
            "wins": 0,
            "win_rate": None,
            "realized_payoff_ratio": None,
            "profit_factor": None,
            "net_pnl_usd": 0.0,
            "maximum_closed_trade_drawdown_usd": 0.0,
            "top_5pct_removed_profit_factor": None,
            "top_5pct_winner_contribution_to_net": None,
            "positive_active_month_share": None,
        }
    wins = values[values > 0]
    losses = -values[values < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(losses.sum())
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    remove_count = int(math.ceil(len(values) * 0.05))
    removed = np.delete(values, np.argsort(values)[-remove_count:])
    removed_profit = float(removed[removed > 0].sum())
    removed_loss = float(-removed[removed < 0].sum())
    months = (
        frame.assign(
            _month=(
                frame["exit_time"]
                .dt.tz_localize(None)
                .dt.to_period("M")
                .astype(str)
            )
        )
        .groupby("_month")[pnl_column]
        .sum()
    )
    net = float(values.sum())
    top_winners = float(np.sort(values)[-remove_count:].sum())
    return {
        "trades": int(len(values)),
        "wins": int(len(wins)),
        "win_rate": float(len(wins) / len(values)),
        "realized_payoff_ratio": (
            float(wins.mean() / losses.mean())
            if len(wins) and len(losses)
            else None
        ),
        "profit_factor": (
            float(gross_profit / gross_loss) if gross_loss else None
        ),
        "net_pnl_usd": net,
        "maximum_closed_trade_drawdown_usd": float(
            np.max(peak - equity)
        ),
        "top_5pct_removed_profit_factor": (
            float(removed_profit / removed_loss)
            if removed_loss
            else None
        ),
        "top_5pct_winner_contribution_to_net": (
            float(top_winners / net) if net else None
        ),
        "positive_active_month_share": float((months > 0).mean()),
    }


def with_cost_haircut(
    frame: pd.DataFrame,
    extra_round_trip_pips: float,
    normalize_to_0p01_lot: bool = False,
) -> pd.DataFrame:
    stressed = frame.copy()
    if normalize_to_0p01_lot:
        pnl = (
            stressed["net_pnl_usd"]
            * (0.01 / stressed["volume"])
        )
        volume_multiplier = 1.0
    else:
        pnl = stressed["net_pnl_usd"]
        volume_multiplier = stressed["volume"] / 0.01
    stressed["scenario_pnl_usd"] = (
        pnl
        - extra_round_trip_pips
        * EURUSD_USD_PER_PIP_AT_0P01_LOT
        * volume_multiplier
    )
    return stressed


def _metric_by(
    frame: pd.DataFrame,
    columns: list[str],
) -> list[dict[str, Any]]:
    rows = []
    grouper: str | list[str] = columns[0] if len(columns) == 1 else columns
    for key, group in frame.groupby(grouper, dropna=False):
        keys = key if isinstance(key, tuple) else (key,)
        rows.append(
            {
                **dict(zip(columns, keys, strict=True)),
                **profit_metrics(group.sort_values("exit_time")),
            }
        )
    return rows


def load_neutral_oracle() -> pd.DataFrame:
    path = (
        PACKAGE_ROOT
        / "outputs"
        / "retrospective_overfit"
        / "FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv"
    )
    frame = pd.read_csv(path)
    for column in ("entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(
            frame[column], utc=True
        ).dt.as_unit("ns")
    return frame[
        frame["regime"].eq("NEUTRAL")
        & frame["entry_time_utc"].between(COMMON_START, COMMON_END)
    ].copy()


def match_oracle(
    predictions: pd.DataFrame,
    oracle: pd.DataFrame,
    tolerance_minutes: int,
) -> pd.DataFrame:
    columns = [
        "prediction_index",
        "fallback_entry_time_utc",
        "fallback_side",
        "fallback_sleeve",
        "oracle_index",
        "oracle_entry_time_utc",
        "oracle_trade_number",
        "absolute_delta_minutes",
    ]
    used: set[int] = set()
    matches: list[dict[str, Any]] = []
    ordered = predictions.sort_values(["entry_time", "side"])
    for prediction_index, row in ordered.iterrows():
        candidates = oracle[
            oracle["side"].eq(row["side"])
            & (
                oracle["entry_time_utc"].dt.date
                == row["entry_time"].date()
            )
        ].copy()
        candidates["delta"] = (
            candidates["entry_time_utc"] - row["entry_time"]
        ).abs()
        candidates = candidates[
            candidates["delta"]
            <= pd.Timedelta(minutes=tolerance_minutes)
        ]
        candidates = candidates[
            ~candidates.index.isin(used)
        ].sort_values(["delta", "entry_time_utc", "oracle_trade_number"])
        if candidates.empty:
            continue
        oracle_index = int(candidates.index[0])
        used.add(oracle_index)
        match = candidates.loc[oracle_index]
        matches.append(
            {
                "prediction_index": int(prediction_index),
                "fallback_entry_time_utc": row["entry_time"],
                "fallback_side": row["side"],
                "fallback_sleeve": row["sleeve"],
                "oracle_index": oracle_index,
                "oracle_entry_time_utc": match["entry_time_utc"],
                "oracle_trade_number": int(
                    match["oracle_trade_number"]
                ),
                "absolute_delta_minutes": float(
                    match["delta"].total_seconds() / 60.0
                ),
            }
        )
    return pd.DataFrame(matches, columns=columns)


def oracle_resemblance(
    trades: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    predictions = trades[
        trades["causal_regime"].eq("NEUTRAL")
        & ~trades["quarantined"]
        & trades["entry_time"].between(COMMON_START, COMMON_END)
    ].copy()
    oracle = load_neutral_oracle()
    exact = match_oracle(predictions, oracle, 0)
    tolerant = match_oracle(predictions, oracle, 15)
    fallback_side = predictions["side"].value_counts()
    oracle_side = oracle["side"].value_counts()
    return (
        {
            "fallback_neutral_trades": int(len(predictions)),
            "fallback_neutral_active_dates": int(
                predictions["entry_time"].dt.date.nunique()
            ),
            "oracle_neutral_trades": int(len(oracle)),
            "oracle_neutral_active_dates": int(
                oracle["entry_time_utc"].dt.date.nunique()
            ),
            "fallback_long_share": float(
                fallback_side.get("LONG", 0) / len(predictions)
            ),
            "oracle_long_share": float(
                oracle_side.get("LONG", 0) / len(oracle)
            ),
            "exact_matches": int(len(exact)),
            "exact_precision": float(
                len(exact) / len(predictions)
            ),
            "exact_recall": float(len(exact) / len(oracle)),
            "same_side_15m_matches": int(len(tolerant)),
            "same_side_15m_precision": float(
                len(tolerant) / len(predictions)
            ),
            "same_side_15m_recall": float(
                len(tolerant) / len(oracle)
            ),
            "fallback_nominal_target_r": 0.80,
            "oracle_nominal_target_r": 1.50,
        },
        tolerant,
    )


def neutral_scenarios(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    neutral = trades[
        trades["causal_regime"].eq("NEUTRAL")
        & ~trades["quarantined"]
        & trades["entry_time"].between(COMMON_START, COMMON_END)
    ].sort_values("exit_time")
    scenarios = {
        "observed_lot_sizing": profit_metrics(neutral),
        "all_trades_fixed_0p01_lot": profit_metrics(
            with_cost_haircut(
                neutral, 0.0, normalize_to_0p01_lot=True
            ),
            "scenario_pnl_usd",
        ),
        "observed_lot_sizing_plus_0p5_pip": profit_metrics(
            with_cost_haircut(neutral, 0.5),
            "scenario_pnl_usd",
        ),
        "fixed_0p01_plus_0p5_pip": profit_metrics(
            with_cost_haircut(
                neutral, 0.5, normalize_to_0p01_lot=True
            ),
            "scenario_pnl_usd",
        ),
    }
    windows = {
        "2024_H2": (
            pd.Timestamp("2024-07-01T00:00:00Z"),
            pd.Timestamp("2024-12-31T23:59:59Z"),
        ),
        "2025": (
            pd.Timestamp("2025-01-01T00:00:00Z"),
            pd.Timestamp("2025-12-31T23:59:59Z"),
        ),
        "2026_H1": (
            pd.Timestamp("2026-01-01T00:00:00Z"),
            pd.Timestamp("2026-06-30T23:59:59Z"),
        ),
    }
    chronological = {}
    for name, (start, end) in windows.items():
        subset = neutral[neutral["exit_time"].between(start, end)]
        chronological[name] = {
            "observed": profit_metrics(subset),
            "plus_0p5_pip": profit_metrics(
                with_cost_haircut(subset, 0.5),
                "scenario_pnl_usd",
            ),
        }
    return {
        "scenarios": scenarios,
        "chronological_slices": chronological,
        "active_dates": int(neutral["entry_time"].dt.date.nunique()),
        "trades_per_active_date": float(
            len(neutral) / neutral["entry_time"].dt.date.nunique()
        ),
    }


def build_result() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg = load_ensemble_config()
    m5, state, manifests = load_inputs(cfg)
    trades = reconstruct_portfolio()
    ledger_check = verify_packaged_ledger(trades)
    offsets = price_time_offset_audit(trades, m5)
    time_audit = selected_time_offset(offsets)
    trades = attach_causal_regime(trades, state, cfg)
    common = trades[
        trades["entry_time"].between(COMMON_START, COMMON_END)
        & ~trades["quarantined"]
    ].copy()
    m15 = trades[trades["sleeve"].eq(M15_SLEEVE)].copy()
    m15["overlay_active"] = m15["volume"].gt(0.01)
    oracle, matches = oracle_resemblance(trades)
    neutral = neutral_scenarios(trades)
    full_stress = {}
    for pips in (0.5, 1.0, 2.0):
        full_stress[f"plus_{str(pips).replace('.', 'p')}_pip"] = (
            profit_metrics(
                with_cost_haircut(trades, pips),
                "scenario_pnl_usd",
            )
        )
    result = {
        "schema_version": "eurusd_adaptive_frequency_fallback_audit_v1",
        "family": FAMILY,
        "audit_date": "2026-07-28",
        "status": "REJECTED_AS_REGIME_1_IMITATION",
        "demo_status": "NO_DEMO_PROMOTION_FROM_THIS_AUDIT",
        "research_boundary": (
            "All observations are adaptive historical development data. "
            "This audit is diagnostic and is not a new holdout."
        ),
        "source_evidence": source_evidence(),
        "packaged_ledger_check": ledger_check,
        "time_normalization": time_audit,
        "raw_report_metrics": {
            "full_portfolio": profit_metrics(trades),
            "m15_sleeve": profit_metrics(
                trades[trades["sleeve"].eq(M15_SLEEVE)]
            ),
            "control_sleeve": profit_metrics(
                trades[trades["sleeve"].eq(CONTROL_SLEEVE)]
            ),
            "common_regime_window": profit_metrics(common),
            "extra_cost_stress": full_stress,
        },
        "floating_drawdown_evidence": {
            "m15_component": report_drawdown(
                FALLBACK_OUTPUT / "M15_TREND_OVERLAY_REPORT.htm"
            ),
            "control_component": report_drawdown(
                FALLBACK_OUTPUT / "CHOP_CONTROL_REPORT.htm"
            ),
            "portfolio_maximum_floating_drawdown_status": (
                "UNKNOWN: the combined reports do not contain a synchronized "
                "portfolio equity curve. Closed-trade drawdown is not a "
                "substitute for portfolio floating drawdown."
            ),
        },
        "regime_attribution": {
            "by_regime": _metric_by(common, ["causal_regime"]),
            "by_sleeve_and_regime": _metric_by(
                common, ["sleeve", "causal_regime"]
            ),
            "m15_overlay_by_regime": _metric_by(
                m15[
                    m15["entry_time"].between(COMMON_START, COMMON_END)
                    & ~m15["quarantined"]
                ],
                ["causal_regime", "overlay_active"],
            ),
        },
        "neutral_regime": neutral,
        "oracle_resemblance": oracle,
        "selection_and_overlap_audit": {
            "m15_trades": int(
                (trades["sleeve"] == M15_SLEEVE).sum()
            ),
            "control_trades": int(
                (trades["sleeve"] == CONTROL_SLEEVE).sum()
            ),
            "m15_share_of_trades": float(
                (trades["sleeve"] == M15_SLEEVE).mean()
            ),
            "doubled_size_m15_trades": int(
                (
                    (trades["sleeve"] == M15_SLEEVE)
                    & trades["volume"].gt(0.01)
                ).sum()
            ),
            "overlay_interpretation": (
                "The H4 overlay changes only requested lot size. It does not "
                "create an independent entry, side, stop, target, or exit."
            ),
            "cross_sleeve_overlap_count_declared": 58,
        },
        "data_manifests": manifests,
        "decision_reasons": [
            (
                "The full portfolio realized payoff ratio is below 1.0 and "
                "does not meet the requested approximately 1.5 payoff."
            ),
            (
                "The best 5% of trades contribute approximately 94% of full "
                "portfolio net profit."
            ),
            (
                "A 0.5-pip extra round-trip haircut reduces full PF below "
                "the old 1.30 adaptive demo floor and winner-removed PF "
                "below 1.0."
            ),
            (
                "The Neutral slice is profitable retrospectively, but "
                "2026 H1 becomes negative after the same 0.5-pip haircut."
            ),
            (
                "The Neutral slice has zero same-side oracle matches within "
                "15 minutes and an almost entirely long side mix."
            ),
            (
                "The doubled-size H4 overlay is conditional leverage on the "
                "same M15 entries, not an independent regime expert."
            ),
            (
                "Combined portfolio floating drawdown cannot be recovered "
                "from the two independent reports."
            ),
        ],
    }
    return (
        serialize(result),
        {
            "TRADES_WITH_CAUSAL_REGIME": trades,
            "TIME_OFFSET_AUDIT": offsets,
            "ORACLE_MATCHES_15M": matches,
        },
    )


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100.0 * value:.2f}%"


def _num(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def render_report(result: dict[str, Any]) -> str:
    full = result["raw_report_metrics"]["full_portfolio"]
    neutral = result["neutral_regime"]["scenarios"]
    observed = neutral["observed_lot_sizing"]
    fixed_stress = neutral["fixed_0p01_plus_0p5_pip"]
    chronological = result["neutral_regime"]["chronological_slices"]
    oracle = result["oracle_resemblance"]
    floating = result["floating_drawdown_evidence"]
    rows = []
    for name in ("2024_H2", "2025", "2026_H1"):
        raw = chronological[name]["observed"]
        stress = chronological[name]["plus_0p5_pip"]
        rows.append(
            f"| {name.replace('_', ' ')} | {raw['trades']} | "
            f"{_pct(raw['win_rate'])} | {_num(raw['realized_payoff_ratio'])} | "
            f"{_num(raw['profit_factor'])} | ${raw['net_pnl_usd']:.2f} | "
            f"{_num(stress['profit_factor'])} | "
            f"${stress['net_pnl_usd']:.2f} |"
        )
    return f"""# EURUSD adaptive frequency fallback audit

Date: `2026-07-28`

Status: `REJECTED_AS_REGIME_1_IMITATION / NO_DEMO_PROMOTION`

The prior Capital.com result is reproducible from the two raw MT5 reports:
`{full['trades']}` trades, `{_pct(full['win_rate'])}` wins, PF
`{_num(full['profit_factor'], 4)}`, and `${full['net_pnl_usd']:.2f}` net.
The audit does not dispute that selected historical result. It rejects the
stronger claim that the portfolio is a robust, independent Regime 1 expert.

## What the headline concealed

- Realized payoff is `{_num(full['realized_payoff_ratio'])}`, not the requested
  approximately `1.5`.
- The best 5% of trades contribute
  `{_pct(full['top_5pct_winner_contribution_to_net'])}` of total net.
- PF after removing those winners is
  `{_num(full['top_5pct_removed_profit_factor'])}`.
- A further 0.5-pip round-trip haircut reduces full PF to
  `{_num(result['raw_report_metrics']['extra_cost_stress']['plus_0p5_pip']['profit_factor'])}`.
- The M15 sleeve supplies
  `{result['selection_and_overlap_audit']['m15_share_of_trades']:.1%}` of all
  trades. Its H4 overlay merely changes the same trade from 0.01 to 0.02 lots;
  it is conditional leverage, not an independent expert.

The MT5 timestamps resolve to UTC: zero hours is the unique minimum-error
alignment for both sleeves against the independent Dukascopy bid/ask M5 cache.

## Causal Neutral / Regime 1 slice

Routing every entry through the exact completed-hour cross-asset classifier used
by the hindsight oracle leaves `{observed['trades']}` Neutral trades:

| Scenario | Trades | Win rate | Payoff | PF | Net | Ex-best-5% PF |
|---|---:|---:|---:|---:|---:|---:|
| Historical sizing | {observed['trades']} | {_pct(observed['win_rate'])} | {_num(observed['realized_payoff_ratio'])} | {_num(observed['profit_factor'])} | ${observed['net_pnl_usd']:.2f} | {_num(observed['top_5pct_removed_profit_factor'])} |
| Every trade 0.01 lot + 0.5 pip | {fixed_stress['trades']} | {_pct(fixed_stress['win_rate'])} | {_num(fixed_stress['realized_payoff_ratio'])} | {_num(fixed_stress['profit_factor'])} | ${fixed_stress['net_pnl_usd']:.2f} | {_num(fixed_stress['top_5pct_removed_profit_factor'])} |

The fixed-size stressed slice remains positive in aggregate, but the
chronological tail does not:

| Slice | Trades | Win rate | Payoff | PF | Net | PF +0.5 pip | Net +0.5 pip |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Oracle resemblance

- Neutral fallback trades: `{oracle['fallback_neutral_trades']}`; Neutral
  oracle trades in the common window: `{oracle['oracle_neutral_trades']}`.
- Exact same-time/same-side matches: `{oracle['exact_matches']}`.
- Same-side matches within 15 minutes: `{oracle['same_side_15m_matches']}`.
- Fallback long share: `{_pct(oracle['fallback_long_share'])}`; oracle long
  share: `{_pct(oracle['oracle_long_share'])}`.
- Fallback nominal target: `0.80R`; oracle nominal target: `1.50R`.

This is profitable mean reversion in one adaptively selected historical slice,
not imitation of the Regime 1 oracle.

## Drawdown and provenance limits

The individual MT5 reports show maximum equity drawdown of
`${floating['m15_component']['maximum_equity_drawdown_usd']:.2f}` for the M15
sleeve and `${floating['control_component']['maximum_equity_drawdown_usd']:.2f}`
for the control. They do not provide a synchronized portfolio equity curve, so
the combined maximum floating drawdown is unknown. The earlier `$28.45` figure
is closed-trade drawdown only.

Source/report hashes match the prior verdict and the compile log says zero
errors and warnings. Source-to-EX5 provenance remains partial because the
scratch compile log does not bind an input-source hash to the packaged EX5
hash.

## Decision

Do not promote this fallback as the Neutral expert. Retain it as a diagnostic
entry hypothesis. Any next test must remove the frequency quota, use fixed
0.01-lot sizing, preserve the causal Neutral gate, target the owner's `1.5R`
payoff directly, and be frozen before its outcome is opened. All archived
history remains development data; only a new prospective shadow period can
provide genuinely untouched confirmation.
"""


def run_audit() -> dict[str, Any]:
    result, artifacts = build_result()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)
    (OUTPUT_ROOT / "RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return result


__all__ = [
    "OUTPUT_ROOT",
    "REPORT_PATH",
    "attach_causal_regime",
    "build_result",
    "match_oracle",
    "profit_metrics",
    "run_audit",
    "with_cost_haircut",
]
