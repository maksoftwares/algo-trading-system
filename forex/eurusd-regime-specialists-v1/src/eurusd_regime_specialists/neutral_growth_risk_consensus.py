from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_binance_eurusdt_flow import load_parent_points
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N46_NEUTRAL_GROWTH_RISK_CONSENSUS"
PREFIXES = ("spx", "copper", "usdcnh")
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_growth_risk_consensus"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_growth_risk_consensus.json"
)
PREREG_LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_GROWTH_RISK_CONSENSUS_PREREG_2026_07_28.sha256.json"
)
DEVELOPMENT_LOCK_PATH = OUTPUT_ROOT / "DEVELOPMENT_GATE_LOCK.sha256.json"
CONFIRMATION_LOCK_PATH = (
    OUTPUT_ROOT / "CONFIRMATION_GATE_LOCK.sha256.json"
)

EURUSD_COLUMNS = (
    "timestamp_ms",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
    "tick_count",
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_prereg_lock() -> dict[str, str]:
    lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_eurusd_outcome") is not True:
        raise RuntimeError("Growth/risk family is not preregistered")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Growth/risk preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_neutral_date_contract"]
    if (
        sha256_file(PACKAGE_ROOT / parent["path"])
        != parent["sha256"]
    ):
        raise RuntimeError("Parent Neutral-date contract drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["paired_source_path"])
        != parent["paired_source_sha256"]
    ):
        raise RuntimeError("Parent Neutral-date source drift")
    eurusd = cfg["eurusd_execution_data_contract"]
    if (
        sha256_file(PACKAGE_ROOT / eurusd["path"])
        != eurusd["sha256"]
    ):
        raise RuntimeError("EURUSD execution contract drift")
    if sha256_file(Path(eurusd["bar_path"])) != eurusd["bar_sha256"]:
        raise RuntimeError("EURUSD M5 source drift")
    source = cfg["growth_risk_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("Growth/risk parquet drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("Growth/risk manifest drift")
    return checked


def _verify_stage_lock(
    path: Path,
    required_flag: str,
    expected_status: str,
) -> dict[str, Any]:
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get(required_flag) is not True:
        raise RuntimeError(f"Stage lock lacks {required_flag}")
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Stage result drift: {relative}")
    result_path = PACKAGE_ROOT / lock["result_path"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != expected_status:
        raise RuntimeError(
            f"Stage lock does not contain {expected_status}"
        )
    return lock


def verify_development_lock() -> dict[str, Any]:
    return _verify_stage_lock(
        DEVELOPMENT_LOCK_PATH,
        "locked_before_2023_outcome",
        "DEVELOPMENT_PASS_CONFIRMATION_LOCK_REQUIRED",
    )


def verify_confirmation_lock() -> dict[str, Any]:
    verify_development_lock()
    return _verify_stage_lock(
        CONFIRMATION_LOCK_PATH,
        "locked_before_2024_2026_outcome",
        "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED",
    )


def safe_neutral_dates() -> pd.DataFrame:
    points = load_parent_points(include_outcomes=False)
    required = {
        "eligible_date",
        "clock_minute",
        "decision_id",
        "entry_time_utc",
    }
    if not required.issubset(points.columns):
        raise RuntimeError("Parent Neutral points lack safe columns")
    prohibited = (
        "outcome",
        "target_first",
        "oracle_member",
        "exit_time",
        "entry_price",
        "target_price",
        "stop_price",
    )
    if any(
        any(token in column for token in prohibited)
        for column in points.columns
    ):
        raise RuntimeError("Outcome column leaked into Neutral source")
    result = (
        points.loc[:, ["eligible_date"]]
        .drop_duplicates()
        .sort_values("eligible_date")
        .reset_index(drop=True)
    )
    result["eligible_date"] = result["eligible_date"].astype(str)
    return result


def growth_risk_columns() -> list[str]:
    columns = ["bar_open_timestamp_ms"]
    for prefix in PREFIXES:
        columns.extend(
            [
                f"{prefix}_available_timestamp_ms",
                f"{prefix}_source_last_timestamp_ms",
                f"{prefix}_return_60m",
            ]
        )
    return columns


def load_growth_risk(cfg: dict[str, Any]) -> pd.DataFrame:
    source = cfg["growth_risk_source"]
    frame = pd.read_parquet(
        Path(source["path"]),
        columns=growth_risk_columns(),
    )
    if frame["bar_open_timestamp_ms"].duplicated().any():
        raise RuntimeError("Growth/risk source has duplicate M5 rows")
    frame["source_bar_open_time_utc"] = pd.to_datetime(
        frame["bar_open_timestamp_ms"], unit="ms", utc=True
    )
    frame["decision_time_utc"] = (
        frame["source_bar_open_time_utc"] + pd.Timedelta(minutes=5)
    )
    return frame.sort_values("source_bar_open_time_utc").reset_index(
        drop=True
    )


def window_name(
    timestamp: pd.Timestamp, cfg: dict[str, Any]
) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE"


def _expected_decisions(
    neutral_dates: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for date in neutral_dates["eligible_date"]:
        day = pd.Timestamp(date, tz="UTC")
        if day.weekday() >= 5:
            continue
        for expert, spec in cfg["experts"].items():
            decision = day + pd.Timedelta(
                hours=int(spec["decision_hour_utc"]),
                minutes=int(spec["decision_minute_utc"]),
            )
            rows.append(
                {
                    "family": FAMILY,
                    "regime": "NEUTRAL",
                    "eligible_date": date,
                    "expert": expert,
                    "decision_time_utc": decision,
                    "source_bar_open_time_utc": (
                        decision - pd.Timedelta(minutes=5)
                    ),
                    "window": window_name(decision, cfg),
                }
            )
    return pd.DataFrame(rows)


def build_candidates(
    neutral_dates: pd.DataFrame,
    growth_risk: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    expected = _expected_decisions(neutral_dates, cfg)
    source_columns = [
        "source_bar_open_time_utc",
        "bar_open_timestamp_ms",
        *[
            column
            for column in growth_risk_columns()
            if column != "bar_open_timestamp_ms"
        ],
    ]
    joined = expected.merge(
        growth_risk.loc[:, source_columns],
        on="source_bar_open_time_utc",
        how="left",
        validate="many_to_one",
    )
    source_present = joined["bar_open_timestamp_ms"].notna()
    decision_timestamp_ms = joined["decision_time_utc"].map(
        lambda value: int(pd.Timestamp(value).value // 1_000_000)
    )
    causal_columns: list[str] = []
    for prefix in PREFIXES:
        causal = f"{prefix}_causal"
        causal_columns.append(causal)
        joined[causal] = (
            source_present
            & joined[f"{prefix}_available_timestamp_ms"].eq(
                joined["bar_open_timestamp_ms"] + 300_000
            )
            & joined[f"{prefix}_available_timestamp_ms"].eq(
                decision_timestamp_ms
            )
            & joined[f"{prefix}_source_last_timestamp_ms"].lt(
                joined[f"{prefix}_available_timestamp_ms"]
            )
            & joined[f"{prefix}_return_60m"].notna()
        )
    all_causal = joined[causal_columns].all(axis=1)
    long_signal = (
        joined["spx_return_60m"].gt(0)
        & joined["copper_return_60m"].gt(0)
        & joined["usdcnh_return_60m"].lt(0)
    )
    short_signal = (
        joined["spx_return_60m"].lt(0)
        & joined["copper_return_60m"].lt(0)
        & joined["usdcnh_return_60m"].gt(0)
    )
    base = load_ensemble_config()
    quarantined = joined["decision_time_utc"].map(
        lambda value: is_quarantined(
            pd.Timestamp(value), "EURUSD", base["quarantine"]
        )
    )
    eligible = (
        all_causal
        & (long_signal | short_signal)
        & joined["window"].ne("OUTSIDE")
        & ~quarantined
    )
    candidates = joined[eligible].copy()
    candidates["side"] = np.where(
        long_signal[eligible], "LONG", "SHORT"
    )
    candidates = candidates[
        [
            "family",
            "regime",
            "eligible_date",
            "expert",
            "decision_time_utc",
            "source_bar_open_time_utc",
            "window",
            "side",
            "spx_return_60m",
            "copper_return_60m",
            "usdcnh_return_60m",
            "spx_available_timestamp_ms",
            "copper_available_timestamp_ms",
            "usdcnh_available_timestamp_ms",
            "spx_source_last_timestamp_ms",
            "copper_source_last_timestamp_ms",
            "usdcnh_source_last_timestamp_ms",
        ]
    ].rename(columns={"decision_time_utc": "entry_time_utc"})
    candidates = candidates.sort_values(
        ["entry_time_utc", "expert"]
    ).reset_index(drop=True)
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_expert = {
        expert: int(candidates["expert"].eq(expert).sum())
        for expert in cfg["experts"]
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    gate = cfg["outcome_blind_census"]
    checks = {
        "total": len(candidates)
        >= int(gate["minimum_candidates_total"]),
        "development": by_window["development_2022"]
        >= int(gate["minimum_candidates_development"]),
        "confirmation": by_window["confirmation_2023"]
        >= int(gate["minimum_candidates_confirmation"]),
        "full_forward_years": all(
            by_window[name]
            >= int(gate["minimum_candidates_each_full_forward_year"])
            for name in ("forward_2024", "forward_2025")
        ),
        "recent_half_year": by_window["recent_2026_h1"]
        >= int(gate["minimum_candidates_recent_half_year"]),
        "both_sides": all(
            by_side[side]
            >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "all_experts": all(
            by_expert[expert]
            >= int(gate["minimum_candidates_each_expert"])
            for expert in cfg["experts"]
        ),
    }
    census = {
        "neutral_dates_total": int(len(neutral_dates)),
        "neutral_dates_in_source_windows": int(
            expected["eligible_date"].nunique()
        ),
        "expected_decision_points": int(len(expected)),
        "source_row_missing_points": int((~source_present).sum()),
        "noncausal_or_incomplete_points": int(
            (source_present & ~all_causal).sum()
        ),
        "causal_complete_points": int(all_causal.sum()),
        "mixed_or_zero_cash_points": int(
            (all_causal & ~(long_signal | short_signal)).sum()
        ),
        "quarantine_cash_points": int(quarantined.sum()),
        "consensus_candidates": int(len(candidates)),
        "candidate_dates": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_expert": by_expert,
        "by_side": by_side,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }
    return candidates, census


def _milliseconds(timestamp: pd.Timestamp) -> int:
    return int(pd.Timestamp(timestamp).value // 1_000_000)


def load_eurusd_stage(
    cfg: dict[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    contract = cfg["eurusd_execution_data_contract"]
    path = Path(contract["bar_path"])
    read_start = start - pd.Timedelta(
        minutes=5
        * int(
            cfg["strategy"][
                "eurusd_stop_lookback_completed_m5_bars"
            ]
        )
    )
    frame = pd.read_parquet(
        path,
        columns=list(EURUSD_COLUMNS),
        filters=[
            ("timestamp_ms", ">=", _milliseconds(read_start)),
            ("timestamp_ms", "<=", _milliseconds(end)),
        ],
    )
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_ms"], unit="ms", utc=True
    )
    frame = (
        frame.sort_values("timestamp_utc")
        .drop_duplicates("timestamp_utc", keep="last")
        .set_index("timestamp_utc")
    )
    if frame.empty:
        raise RuntimeError("Bounded EURUSD stage load returned no bars")
    if frame.index.min() < read_start or frame.index.max() > end:
        raise RuntimeError("Bounded EURUSD stage load crossed its firewall")
    return frame, {
        "path": str(path),
        "sha256": contract["bar_sha256"],
        "requested_start_utc": start,
        "read_start_with_stop_lookback_utc": read_start,
        "stage_end_utc": end,
        "loaded_first_timestamp_utc": frame.index.min(),
        "loaded_last_timestamp_utc": frame.index.max(),
        "loaded_rows": int(len(frame)),
        "future_rows_loaded": False,
    }


def _effective_ask(
    bar: pd.Series, field: str, spread_floor: float
) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def _walk_exit(
    m5: pd.DataFrame,
    start_position: int,
    last_bar_time: pd.Timestamp,
    side: str,
    stop: float,
    target: float,
    spread_floor: float,
    slippage: float,
    hold_hours: float,
) -> tuple[pd.Timestamp, float, str]:
    end_position = min(
        max(
            int(
                m5.index.searchsorted(
                    last_bar_time, side="right"
                )
            )
            - 1,
            start_position,
        ),
        len(m5) - 1,
    )
    for position in range(start_position, end_position + 1):
        timestamp = m5.index[position]
        bar = m5.iloc[position]
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                return (
                    timestamp,
                    min(float(bar["bid_open"]), stop) - slippage,
                    "STOP",
                )
            if float(bar["bid_high"]) >= target:
                return (
                    timestamp,
                    max(float(bar["bid_open"]), target) - slippage,
                    "TARGET",
                )
        else:
            ask_open = _effective_ask(bar, "open", spread_floor)
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            if ask_high >= stop:
                return (
                    timestamp,
                    max(ask_open, stop) + slippage,
                    "STOP",
                )
            if ask_low <= target:
                return (
                    timestamp,
                    min(ask_open, target) + slippage,
                    "TARGET",
                )
    bar = m5.iloc[end_position]
    actual_close = m5.index[end_position] + pd.Timedelta(minutes=5)
    if side == "LONG":
        return (
            actual_close,
            float(bar["bid_close"]) - slippage,
            f"TIME_{hold_hours:g}H",
        )
    return (
        actual_close,
        _effective_ask(bar, "close", spread_floor) + slippage,
        f"TIME_{hold_hours:g}H",
    )


def simulate(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    lookback = int(
        strategy["eurusd_stop_lookback_completed_m5_bars"]
    )
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    buffer = float(strategy["stop_buffer_pips"]) * PIP
    risk_floor = float(strategy["stop_floor_pips"]) * PIP
    risk_ceiling = float(strategy["stop_ceiling_pips"]) * PIP
    target_r = float(strategy["target_r"])
    hold_hours = float(strategy["maximum_hold_hours"])
    hold = pd.Timedelta(hours=hold_hours)
    one_bar = pd.Timedelta(minutes=5)
    open_until: pd.Timestamp | None = None
    records: list[dict[str, Any]] = []
    skips = {
        "position_open": 0,
        "entry_bar_missing": 0,
        "prior_structure_missing_or_noncontiguous": 0,
        "risk_ceiling": 0,
    }
    for _, candidate in candidates.sort_values(
        ["entry_time_utc", "expert"]
    ).iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time < open_until:
            skips["position_open"] += 1
            continue
        position = int(
            m5.index.searchsorted(entry_time, side="left")
        )
        if position >= len(m5) or m5.index[position] != entry_time:
            skips["entry_bar_missing"] += 1
            continue
        prior = m5.iloc[max(0, position - lookback) : position]
        expected_prior = pd.date_range(
            entry_time - pd.Timedelta(minutes=5 * lookback),
            periods=lookback,
            freq="5min",
        )
        if (
            len(prior) != lookback
            or not prior.index.equals(expected_prior)
        ):
            skips["prior_structure_missing_or_noncontiguous"] += 1
            continue
        bar = m5.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = (
                _effective_ask(bar, "open", spread_floor)
                + slippage
            )
            raw_stop = float(prior["bid_low"].min()) - buffer
            raw_risk = entry - raw_stop
            risk = max(raw_risk, risk_floor)
            stop = entry - risk
            target = entry + target_r * risk
        else:
            entry = float(bar["bid_open"]) - slippage
            prior_ask_high = max(
                _effective_ask(row, "high", spread_floor)
                for _, row in prior.iterrows()
            )
            raw_stop = prior_ask_high + buffer
            raw_risk = raw_stop - entry
            risk = max(raw_risk, risk_floor)
            stop = entry + risk
            target = entry - target_r * risk
        if not math.isfinite(risk) or risk > risk_ceiling:
            skips["risk_ceiling"] += 1
            continue
        exit_time, exit_price, exit_reason = _walk_exit(
            m5,
            position,
            entry_time + hold - one_bar,
            side,
            stop,
            target,
            spread_floor,
            slippage,
            hold_hours,
        )
        pnl = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        records.append(
            {
                "family": FAMILY,
                "expert": candidate["expert"],
                "regime": "NEUTRAL",
                "eligible_date": candidate["eligible_date"],
                "side": side,
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "risk_distance": risk,
                "risk_pips": risk / PIP,
                "r": result_r,
                "extra_half_pip_stress_r": (
                    result_r
                    - float(
                        execution[
                            "extra_round_trip_stress_pips"
                        ]
                    )
                    * PIP
                    / risk
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
                "spx_return_60m": candidate["spx_return_60m"],
                "copper_return_60m": candidate[
                    "copper_return_60m"
                ],
                "usdcnh_return_60m": candidate[
                    "usdcnh_return_60m"
                ],
            }
        )
        open_until = exit_time
    return pd.DataFrame(records), skips


def _window(
    frame: pd.DataFrame,
    bounds: list[str],
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame[
        frame["entry_time_utc"].between(
            pd.Timestamp(bounds[0]),
            pd.Timestamp(bounds[1]),
            inclusive="both",
        )
    ].copy()


def stage_metrics(
    trades: pd.DataFrame,
    gate: dict[str, Any],
    experts: list[str],
) -> dict[str, Any]:
    overall = payoff_metrics(trades)
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    by_expert = {
        expert: payoff_metrics(
            trades[trades["expert"].eq(expert)]
        )
        for expert in experts
    }
    checks = {
        "minimum_trades": overall["trades"]
        >= int(gate["minimum_trades"]),
        "win_rate_band": (
            overall["win_rate"] >= float(gate["minimum_win_rate"])
            and overall["win_rate"] <= float(gate["maximum_win_rate"])
        ),
        "realized_payoff_band": (
            overall["realized_payoff_ratio"]
            >= float(gate["minimum_realized_payoff_ratio"])
            and overall["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
        ),
        "profit_factor": overall["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "positive_expectancy": overall["expectancy_r"]
        > float(gate["minimum_expectancy_r"]),
        "side_trade_capacity": all(
            block["trades"] >= int(gate["minimum_each_side_trades"])
            for block in by_side.values()
        ),
        "side_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for block in by_side.values()
        ),
        "drawdown": overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"]),
    }
    return {
        "overall": overall,
        "by_side": by_side,
        "by_expert": by_expert,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def _source_manifest(cfg: dict[str, Any]) -> dict[str, Any]:
    source = cfg["growth_risk_source"]
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    return {
        "origin": source["origin"],
        "path": source["path"],
        "sha256": source["sha256"],
        "manifest_path": source["manifest_path"],
        "manifest_sha256": source["manifest_sha256"],
        "schema_version": manifest["schema_version"],
        "rows": int(manifest["rows"]),
        "first_bar_open_timestamp_ms": int(
            manifest["first_bar_open_timestamp_ms"]
        ),
        "last_bar_open_timestamp_ms": int(
            manifest["last_bar_open_timestamp_ms"]
        ),
        "paid_data_used": bool(manifest["paid_data_used"]),
        "databento_used": bool(manifest["databento_used"]),
    }


def _load_outcome_blind_inputs() -> tuple[
    dict[str, Any], pd.DataFrame, pd.DataFrame
]:
    cfg = load_config()
    neutral_dates = safe_neutral_dates()
    growth_risk = load_growth_risk(cfg)
    return cfg, neutral_dates, growth_risk


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    verify_prereg_lock()
    cfg, neutral_dates, growth_risk = _load_outcome_blind_inputs()
    candidates, census = build_candidates(
        neutral_dates, growth_risk, cfg
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_consensus_census_v1"
        ),
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_DEVELOPMENT_ALLOWED"
            if census["passed"]
            else "CENSUS_FAIL_NO_EURUSD_PNL_ALLOWED"
        ),
        "census": census,
        "growth_risk_source": _source_manifest(cfg),
        "eurusd_outcomes_loaded": False,
        "broker_action_allowed": False,
    }
    return serialize(result), candidates


def run_development() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    cfg, neutral_dates, growth_risk = _load_outcome_blind_inputs()
    candidates, census = build_candidates(
        neutral_dates, growth_risk, cfg
    )
    if not census["passed"]:
        raise RuntimeError("Census failed; EURUSD P&L is forbidden")
    name = cfg["development_gate"]["allowed_window"]
    bounds = cfg["windows"][name]
    stage_candidates = _window(candidates, bounds)
    start, end = map(pd.Timestamp, bounds)
    m5, eurusd_load = load_eurusd_stage(cfg, start, end)
    trades, skips = simulate(stage_candidates, m5, cfg)
    metrics = stage_metrics(
        trades,
        cfg["development_gate"],
        list(cfg["experts"]),
    )
    status = (
        "DEVELOPMENT_PASS_CONFIRMATION_LOCK_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_DEVELOPMENT_2023_2026_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_development_v1"
        ),
        "family": FAMILY,
        "status": status,
        "census": census,
        "stage": name,
        "stage_bounds": bounds,
        "development": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": eurusd_load,
        "later_eurusd_outcomes_loaded": False,
        "growth_risk_source": _source_manifest(cfg),
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "DEVELOPMENT_CANDIDATES": stage_candidates,
        "DEVELOPMENT_TRADES": trades,
    }


def run_confirmation() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    verify_development_lock()
    cfg, neutral_dates, growth_risk = _load_outcome_blind_inputs()
    candidates, census = build_candidates(
        neutral_dates, growth_risk, cfg
    )
    name = cfg["confirmation_gate"]["allowed_window"]
    bounds = cfg["windows"][name]
    stage_candidates = _window(candidates, bounds)
    start, end = map(pd.Timestamp, bounds)
    m5, eurusd_load = load_eurusd_stage(cfg, start, end)
    trades, skips = simulate(stage_candidates, m5, cfg)
    metrics = stage_metrics(
        trades,
        cfg["confirmation_gate"],
        list(cfg["experts"]),
    )
    status = (
        "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CONFIRMATION_2024_2026_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_confirmation_v1"
        ),
        "family": FAMILY,
        "status": status,
        "stage": name,
        "stage_bounds": bounds,
        "confirmation": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": eurusd_load,
        "forward_eurusd_outcomes_loaded": False,
        "growth_risk_source": _source_manifest(cfg),
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "CONFIRMATION_CANDIDATES": stage_candidates,
        "CONFIRMATION_TRADES": trades,
    }


def same_day_same_side_oracle_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    actual = oracle.reset_index(drop=True)
    unmatched = set(actual.index)
    records: list[dict[str, Any]] = []
    for trade_index, trade in trades.sort_values(
        "entry_time_utc"
    ).iterrows():
        matches = [
            index
            for index in unmatched
            if str(actual.at[index, "side"]) == str(trade["side"])
            and pd.Timestamp(
                actual.at[index, "entry_time_utc"]
            ).date()
            == pd.Timestamp(trade["entry_time_utc"]).date()
        ]
        if not matches:
            continue
        chosen = min(
            matches,
            key=lambda index: abs(
                pd.Timestamp(actual.at[index, "entry_time_utc"])
                - pd.Timestamp(trade["entry_time_utc"])
            ),
        )
        unmatched.remove(chosen)
        records.append(
            {
                "trade_index": int(trade_index),
                "trade_entry_time_utc": trade["entry_time_utc"],
                "trade_side": trade["side"],
                "oracle_entry_time_utc": actual.at[
                    chosen, "entry_time_utc"
                ],
                "absolute_difference_minutes": abs(
                    pd.Timestamp(actual.at[chosen, "entry_time_utc"])
                    - pd.Timestamp(trade["entry_time_utc"])
                ).total_seconds()
                / 60.0,
            }
        )
    matches = len(records)
    precision = matches / len(trades) if len(trades) else 0.0
    recall = matches / len(actual) if len(actual) else 0.0
    return {
        "predicted_trades": int(len(trades)),
        "oracle_trades": int(len(actual)),
        "matches": int(matches),
        "precision": float(precision),
        "recall": float(recall),
    }, pd.DataFrame(records)


def forward_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    names = ("forward_2024", "forward_2025", "recent_2026_h1")
    windows = {
        name: payoff_metrics(_window(trades, cfg["windows"][name]))
        for name in names
    }
    overall = payoff_metrics(trades)
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    by_expert = {
        expert: payoff_metrics(
            trades[trades["expert"].eq(expert)]
        )
        for expert in cfg["experts"]
    }
    top_removed = payoff_metrics(remove_top_winners(trades))
    stressed = payoff_metrics(
        trades, value_column="extra_half_pip_stress_r"
    )
    oracle_metrics, oracle_matches = (
        same_day_same_side_oracle_metrics(trades, oracle)
    )
    gate = cfg["forward_admission"]
    checks = {
        "window_trade_capacity": (
            windows["forward_2024"]["trades"]
            >= int(gate["minimum_trades_each_full_year"])
            and windows["forward_2025"]["trades"]
            >= int(gate["minimum_trades_each_full_year"])
            and windows["recent_2026_h1"]["trades"]
            >= int(gate["minimum_trades_recent_half_year"])
        ),
        "overall_win_rate_band": (
            overall["win_rate"]
            >= float(gate["minimum_overall_win_rate"])
            and overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "overall_realized_payoff_band": (
            overall["realized_payoff_ratio"]
            >= float(
                gate["minimum_overall_realized_payoff_ratio"]
            )
            and overall["realized_payoff_ratio"]
            <= float(
                gate["maximum_overall_realized_payoff_ratio"]
            )
        ),
        "overall_profit_factor": overall["profit_factor"]
        >= float(gate["minimum_overall_profit_factor"]),
        "each_window_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            for block in windows.values()
        ),
        "side_trade_capacity": all(
            block["trades"]
            >= int(gate["minimum_each_side_trades"])
            for block in by_side.values()
        ),
        "side_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for block in by_side.values()
        ),
        "drawdown": overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"]),
        "top_winners_removed": top_removed["profit_factor"]
        >= float(
            gate["minimum_top_5pct_removed_profit_factor"]
        ),
        "extra_half_pip": stressed["profit_factor"]
        >= float(gate["minimum_extra_half_pip_profit_factor"]),
        "oracle_precision": oracle_metrics["precision"]
        >= float(
            gate["minimum_same_day_same_side_oracle_precision"]
        ),
    }
    return {
        "overall": overall,
        "windows": windows,
        "by_side": by_side,
        "by_expert": by_expert,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
        "same_day_same_side_oracle": oracle_metrics,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }, oracle_matches


def load_oracle_forward(
    cfg: dict[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    contract = cfg["oracle_source"]
    path = PACKAGE_ROOT / contract["path"]
    if sha256_file(path) != contract["sha256"]:
        raise RuntimeError("Oracle source drift")
    oracle = pd.read_csv(path)
    oracle["entry_time_utc"] = pd.to_datetime(
        oracle["entry_time_utc"], utc=True
    )
    if "regime" in oracle.columns:
        oracle = oracle[oracle["regime"].eq("NEUTRAL")]
    return oracle[
        oracle["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ].copy()


def run_forward() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    verify_confirmation_lock()
    cfg, neutral_dates, growth_risk = _load_outcome_blind_inputs()
    candidates, _ = build_candidates(
        neutral_dates, growth_risk, cfg
    )
    start = pd.Timestamp(cfg["windows"]["forward_2024"][0])
    end = pd.Timestamp(cfg["windows"]["recent_2026_h1"][1])
    stage_candidates = candidates[
        candidates["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ].copy()
    m5, eurusd_load = load_eurusd_stage(cfg, start, end)
    trades, skips = simulate(stage_candidates, m5, cfg)
    oracle = load_oracle_forward(cfg, start, end)
    metrics, oracle_matches = forward_metrics(
        trades, oracle, cfg
    )
    status = (
        "HISTORICAL_FORWARD_PASS_PROSPECTIVE_SHADOW_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CHRONOLOGICAL_FORWARD_NO_RETUNING"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_forward_v1"
        ),
        "family": FAMILY,
        "status": status,
        "forward": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": eurusd_load,
        "last_six_months": metrics["windows"][
            "recent_2026_h1"
        ],
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "FORWARD_CANDIDATES": stage_candidates,
        "FORWARD_TRADES": trades,
        "ORACLE_MATCHES": oracle_matches,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "CONFIRMATION_LOCK_PATH",
    "DEVELOPMENT_LOCK_PATH",
    "OUTPUT_ROOT",
    "build_candidates",
    "forward_metrics",
    "load_config",
    "load_eurusd_stage",
    "run_census",
    "run_confirmation",
    "run_development",
    "run_forward",
    "same_day_same_side_oracle_metrics",
    "simulate",
    "stage_metrics",
    "verify_confirmation_lock",
    "verify_development_lock",
    "verify_prereg_lock",
    "write_json",
]
