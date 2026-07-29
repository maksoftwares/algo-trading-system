from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .adaptive_frequency_audit import attach_causal_regime
from .ensemble import load_ensemble_config
from .research import PACKAGE_ROOT, load_inputs

FAMILY = "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_V1"
CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_neutral_rates_dollar_sign_consensus_h4.json"
)
PREREG_LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_rates_dollar_sign_consensus_h4"
CENSUS_PATH = OUTPUT_ROOT / "CENSUS.json"
CANDIDATES_PATH = OUTPUT_ROOT / "CANDIDATES.csv"
CONTEXT_PATH = OUTPUT_ROOT / "LAGGED_DAILY_CONTEXT.csv"
CENSUS_REPORT_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_CENSUS_2026_07_29.md"
)
CENSUS_LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_SIGN_CONSENSUS_H4_CENSUS_RESULT_"
    "2026_07_29.sha256.json"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_prereg_lock() -> dict[str, Any]:
    lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_census_and_forward_outcomes") is not True
        or lock.get("pnl_or_forward_path_loaded") is not False
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("parameter_search_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Sign-consensus preregistration lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Sign-consensus prereg drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def _source_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (PACKAGE_ROOT / path).resolve()


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    checked: dict[str, str] = {}
    for name, source in config["sources"].items():
        path = _source_path(source["path"])
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise RuntimeError(f"Sign-consensus source drift: {name}")
        checked[name] = actual
        if "manifest_path" in source:
            manifest = _source_path(source["manifest_path"])
            manifest_hash = sha256_file(manifest)
            if manifest_hash != source["manifest_sha256"]:
                raise RuntimeError(f"Sign-consensus manifest drift: {name}")
            checked[f"{name}_manifest"] = manifest_hash
    return checked


def _ratio_by_date(
    paths: list[Path],
    numerator: str,
    denominator: str,
) -> dict[pd.Timestamp, float]:
    values: dict[pd.Timestamp, float] = {}
    for path in paths:
        frame = pd.read_csv(
            path,
            usecols=["date_utc", numerator, denominator],
        )
        frame["date_utc"] = pd.to_datetime(
            frame["date_utc"], errors="raise"
        ).dt.normalize()
        frame[numerator] = pd.to_numeric(frame[numerator], errors="raise")
        frame[denominator] = pd.to_numeric(frame[denominator], errors="raise")
        frame = frame[frame[numerator].gt(0) & frame[denominator].gt(0)]
        for row in frame.itertuples(index=False):
            values[pd.Timestamp(row.date_utc)] = float(
                getattr(row, numerator) / getattr(row, denominator)
            )
    return values


def build_lagged_context(config: dict[str, Any]) -> pd.DataFrame:
    sources = config["sources"]
    uup = _ratio_by_date(
        [
            _source_path(sources["tlt_uup_reference"]["path"]),
            _source_path(sources["tlt_uup_recent"]["path"]),
        ],
        "tlt_close",
        "uup_close",
    )
    shy = _ratio_by_date(
        [
            _source_path(sources["tlt_shy_reference"]["path"]),
            _source_path(sources["tlt_shy_recent"]["path"]),
        ],
        "tlt_close",
        "shy_close",
    )
    dates = sorted(set(uup).intersection(shy))
    records: list[dict[str, Any]] = []
    for index in range(20, len(dates)):
        date = dates[index]
        records.append(
            {
                "available_time_utc": (date.tz_localize("UTC") + pd.Timedelta(days=1)),
                "observation_date": date.date().isoformat(),
                "tlt_uup_5d_pct": ((uup[date] / uup[dates[index - 5]]) - 1.0) * 100.0,
                "tlt_uup_20d_pct": ((uup[date] / uup[dates[index - 20]]) - 1.0) * 100.0,
                "tlt_shy_20d_pct": ((shy[date] / shy[dates[index - 20]]) - 1.0) * 100.0,
            }
        )
    context = pd.DataFrame(records).sort_values("available_time_utc")
    if context.empty or context["available_time_utc"].duplicated().any():
        raise RuntimeError("Invalid lagged rates/dollar context")
    context["available_time_utc"] = context["available_time_utc"].dt.as_unit("ns")
    return context.reset_index(drop=True)


def load_eurusd_m5(config: dict[str, Any]) -> pd.DataFrame:
    source = config["sources"]["eurusd_m5"]
    path = _source_path(source["path"])
    frame = pd.read_parquet(
        path,
        columns=[
            "timestamp_ms",
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        ],
    )
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame = frame.set_index("timestamp_utc").sort_index()
    if frame.index.duplicated().any():
        raise RuntimeError("Duplicate EURUSD M5 timestamps")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_utc"])
    return frame.loc[(frame.index >= start) & (frame.index <= end)].copy()


def build_h4_features(m5: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    construction = config["h4_construction"]
    grouped = m5.resample(
        construction["bar_rule"],
        closed=construction["closed"],
        label=construction["label"],
    )
    h4 = grouped.agg(
        bid_open=("bid_open", "first"),
        bid_high=("bid_high", "max"),
        bid_low=("bid_low", "min"),
        bid_close=("bid_close", "last"),
        m5_rows=("bid_open", "count"),
    )
    h4 = h4[h4["m5_rows"].ge(int(construction["minimum_m5_rows_per_h4_bar"]))].copy()
    strategy = config["strategy"]
    for period, name in (
        (strategy["ema_fast_period"], "ema20"),
        (strategy["ema_mid_period"], "ema50"),
        (strategy["ema_slow_period"], "ema100"),
    ):
        h4[name] = (
            h4["bid_close"]
            .ewm(
                span=int(period),
                adjust=bool(construction["ema_adjust"]),
                min_periods=int(period),
            )
            .mean()
        )
    previous_close = h4["bid_close"].shift(1)
    true_range = pd.concat(
        [
            h4["bid_high"] - h4["bid_low"],
            (h4["bid_high"] - previous_close).abs(),
            (h4["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_period = int(strategy["atr_period"])
    h4["atr"] = true_range.ewm(
        alpha=1.0 / atr_period,
        adjust=False,
        min_periods=atr_period,
    ).mean()
    recent_bars = int(strategy["recent_extreme_bars_including_signal"])
    h4["recent_low"] = h4["bid_low"].rolling(recent_bars, min_periods=recent_bars).min()
    h4["recent_high"] = (
        h4["bid_high"].rolling(recent_bars, min_periods=recent_bars).max()
    )
    h4.index.name = "signal_time_utc"
    return h4


def create_signal_candidates(
    h4: pd.DataFrame,
    context: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    strategy = config["strategy"]
    features = h4.reset_index().sort_values("signal_time_utc")
    features["signal_time_utc"] = features["signal_time_utc"].dt.as_unit("ns")
    context = context.copy()
    context["available_time_utc"] = context["available_time_utc"].dt.as_unit("ns")
    features = pd.merge_asof(
        features,
        context.sort_values("available_time_utc"),
        left_on="signal_time_utc",
        right_on="available_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    features["entry_time"] = features["signal_time_utc"] + pd.Timedelta(hours=4)
    features = features[
        features["entry_time"].dt.hour.isin(strategy["allowed_entry_hours_utc"])
    ].copy()
    long_macro = (
        features["tlt_uup_5d_pct"].gt(0)
        & features["tlt_uup_20d_pct"].gt(0)
        & features["tlt_shy_20d_pct"].gt(0)
    )
    short_macro = (
        features["tlt_uup_5d_pct"].lt(0)
        & features["tlt_uup_20d_pct"].lt(0)
        & features["tlt_shy_20d_pct"].lt(0)
    )
    long_price = (
        features["ema20"].gt(features["ema50"])
        & features["ema50"].gt(features["ema100"])
        & features["bid_low"].le(features["ema20"] + 0.25 * features["atr"])
        & features["bid_close"].gt(features["bid_open"])
        & features["bid_close"].gt(features["ema20"])
    )
    short_price = (
        features["ema20"].lt(features["ema50"])
        & features["ema50"].lt(features["ema100"])
        & features["bid_high"].ge(features["ema20"] - 0.25 * features["atr"])
        & features["bid_close"].lt(features["bid_open"])
        & features["bid_close"].lt(features["ema20"])
    )
    selected = features[long_macro & long_price | short_macro & short_price]
    selected = selected.copy()
    selected["side"] = np.where(long_macro.loc[selected.index], "LONG", "SHORT")
    atr_multiple = float(strategy["stop_atr_multiple"])
    selected["planned_stop_price"] = np.where(
        selected["side"].eq("LONG"),
        np.minimum(
            selected["recent_low"],
            selected["bid_close"] - atr_multiple * selected["atr"],
        ),
        np.maximum(
            selected["recent_high"],
            selected["bid_close"] + atr_multiple * selected["atr"],
        ),
    )
    selected["sleeve"] = "RATES_DOLLAR_SIGN_CONSENSUS_H4"
    selected["exit_time"] = selected["entry_time"]
    columns = [
        "entry_time",
        "exit_time",
        "signal_time_utc",
        "sleeve",
        "side",
        "planned_stop_price",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "atr",
        "ema20",
        "ema50",
        "ema100",
        "recent_low",
        "recent_high",
        "available_time_utc",
        "observation_date",
        "tlt_uup_5d_pct",
        "tlt_uup_20d_pct",
        "tlt_shy_20d_pct",
    ]
    return selected[columns].sort_values("entry_time").reset_index(drop=True)


def attach_neutral_ownership(
    candidates: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    classifier_config = load_ensemble_config()
    _, state, manifests = load_inputs(classifier_config)
    owned = attach_causal_regime(candidates, state, classifier_config)
    return owned, manifests


def _period(frame: pd.DataFrame, bounds: list[str]) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[frame["entry_time"].between(start, end, inclusive="both")]


def census_summary(owned: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    eligible = owned[
        owned["causal_regime"].eq(config["owned_regime"]) & ~owned["quarantined"]
    ].copy()
    windows = {
        name: len(_period(eligible, bounds))
        for name, bounds in config["windows"].items()
    }
    side_counts = {
        side: int(eligible["side"].eq(side).sum())
        for side in config["strategy"]["directions"]
    }
    gates = config["outcome_blind_census"]
    gate_results = {
        "minimum_neutral_signals_total": len(eligible)
        >= int(gates["minimum_neutral_signals_total"]),
        "minimum_neutral_signals_development": windows["DEVELOPMENT_2019_2022"]
        >= int(gates["minimum_neutral_signals_development"]),
        "minimum_neutral_signals_each_full_oos_year": all(
            windows[name] >= int(gates["minimum_neutral_signals_each_full_oos_year"])
            for name in ("OOS_2023", "OOS_2024", "OOS_2025")
        ),
        "minimum_neutral_signals_recent_half_year": windows["OOS_2026_H1"]
        >= int(gates["minimum_neutral_signals_recent_half_year"]),
        "minimum_neutral_signals_each_side": all(
            count >= int(gates["minimum_neutral_signals_each_side"])
            for count in side_counts.values()
        ),
    }
    regime_counts = {
        str(key): int(value)
        for key, value in owned["causal_regime"]
        .value_counts(dropna=False)
        .sort_index()
        .items()
    }
    return {
        "all_directional_signals": len(owned),
        "eligible_neutral_signals": len(eligible),
        "active_neutral_dates": int(eligible["entry_time"].dt.date.nunique()),
        "neutral_signals_per_active_date": (
            float(len(eligible) / eligible["entry_time"].dt.date.nunique())
            if len(eligible)
            else 0.0
        ),
        "by_side": side_counts,
        "by_window": windows,
        "by_causal_regime": regime_counts,
        "quarantined_neutral_signals": int(
            (
                owned["causal_regime"].eq(config["owned_regime"]) & owned["quarantined"]
            ).sum()
        ),
        "gate_results": gate_results,
        "all_census_gates_passed": bool(all(gate_results.values())),
    }


def build_census() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    lock = verify_prereg_lock()
    config = load_config()
    source_hashes = verify_sources(config)
    context = build_lagged_context(config)
    m5 = load_eurusd_m5(config)
    h4 = build_h4_features(m5, config)
    raw_candidates = create_signal_candidates(h4, context, config)
    owned, classifier_manifests = attach_neutral_ownership(raw_candidates)
    eligible = owned[
        owned["causal_regime"].eq(config["owned_regime"]) & ~owned["quarantined"]
    ].copy()
    eligible["entry_time_utc"] = eligible["entry_time"]
    summary = census_summary(owned, config)
    status = (
        "CENSUS_CAPACITY_PASS_EXECUTION_FREEZE_ALLOWED"
        if summary["all_census_gates_passed"]
        else "REJECTED_OUTCOME_BLIND_CAPACITY_CENSUS"
    )
    result = {
        "schema_version": ("eurusd_neutral_rates_dollar_sign_consensus_h4_census_v1"),
        "status": status,
        "campaign_id": config["campaign_id"],
        "frozen_at_utc": config["frozen_at_utc"],
        "prereg_lock_verified": True,
        "prereg_checked_files": lock["checked_files"],
        "source_hashes_verified": source_hashes,
        "classifier_input_manifests": classifier_manifests,
        "context": {
            "rows": len(context),
            "first_available_time_utc": context["available_time_utc"].min(),
            "last_available_time_utc": context["available_time_utc"].max(),
            "next_calendar_day_utc_lag_enforced": True,
        },
        "h4": {
            "bars": len(h4),
            "first_bar_utc": h4.index.min(),
            "last_bar_utc": h4.index.max(),
        },
        "summary": summary,
        "boundary": {
            "forward_trade_path_evaluated": False,
            "stop_or_target_outcome_evaluated": False,
            "pnl_loaded_or_computed": False,
            "oracle_loaded": False,
            "parameter_search_performed": False,
            "threshold_search_performed": False,
            "direction_selected_by_outcome": False,
            "frequency_target_enforced": False,
            "broker_action_performed": False,
        },
        "execution_allowed": bool(summary["all_census_gates_passed"]),
        "historical_census_can_authorize_demo": False,
    }
    return result, eligible, context


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def render_census_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# EURUSD Neutral rates/dollar sign-consensus H4 census",
        "",
        f"Status: `{result['status']}`",
        "",
        "## Outcome-blind capacity",
        "",
        "| Total Neutral signals | Active dates | Long | Short |",
        "|---:|---:|---:|---:|",
        (
            f"| {summary['eligible_neutral_signals']} | "
            f"{summary['active_neutral_dates']} | "
            f"{summary['by_side']['LONG']} | "
            f"{summary['by_side']['SHORT']} |"
        ),
        "",
        "| Window | Signals |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name} | {count} |" for name, count in summary["by_window"].items()
    )
    lines.extend(
        [
            "",
            "## Frozen gates",
            "",
        ]
    )
    lines.extend(
        f"- `{name}`: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in summary["gate_results"].items()
    )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Only completed H4 inputs, lagged daily context, timestamps, sides, and causal regime ownership were counted.",
            "- No post-entry path, stop, target, P&L, or oracle match was evaluated.",
            "- No threshold, direction, hour, date, or regime was selected after viewing an outcome.",
            "- No broker, demo, or live action occurred.",
            "",
        ]
    )
    return "\n".join(lines)


def write_census(
    result: dict[str, Any],
    candidates: pd.DataFrame,
    context: pd.DataFrame,
) -> dict[str, Any]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    CENSUS_PATH.write_text(
        json.dumps(_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    candidates.to_csv(CANDIDATES_PATH, index=False)
    context.to_csv(CONTEXT_PATH, index=False)
    CENSUS_REPORT_PATH.write_text(render_census_report(result), encoding="utf-8")
    lock = {
        "family": FAMILY,
        "status": result["status"],
        "census_completed_before_forward_outcomes": True,
        "pnl_or_forward_path_loaded": False,
        "oracle_loaded": False,
        "execution_allowed": result["execution_allowed"],
        "files": {
            str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/"): (sha256_file(path))
            for path in (
                CENSUS_PATH,
                CANDIDATES_PATH,
                CONTEXT_PATH,
                CENSUS_REPORT_PATH,
            )
        },
    }
    CENSUS_LOCK_PATH.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return lock


def run_census() -> dict[str, Any]:
    result, candidates, context = build_census()
    lock = write_census(result, candidates, context)
    return {**result, "census_result_lock": lock}


__all__ = [
    "build_h4_features",
    "build_lagged_context",
    "census_summary",
    "create_signal_candidates",
    "load_config",
    "run_census",
    "verify_prereg_lock",
    "verify_sources",
    "write_census",
]
