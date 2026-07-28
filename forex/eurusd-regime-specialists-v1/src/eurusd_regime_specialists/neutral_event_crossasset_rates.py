from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_macro_event_drift import (
    load_config as load_event_config,
    load_event_source,
    qualifying_events,
)
from .neutral_symmetric_rsi_1p5r import (
    _effective_ask,
    _walk_exit,
    oracle_metrics,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    load_inputs,
    serialize,
    sha256_file,
)


FAMILY = "N35_NEUTRAL_EVENT_CROSSASSET_RATES"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_event_crossasset_rates"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_event_crossasset_rates.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_EVENT_CROSSASSET_RATES_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("Event cross-asset contract is not outcome-locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Event cross-asset preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in ("data_and_classifier_contract", "event_clock_contract"):
        reference = cfg[key]
        actual = sha256_file(PACKAGE_ROOT / reference["path"])
        if actual != reference["sha256"]:
            raise RuntimeError(f"{key} drift")
    for key in ("event_source", "crossasset_source"):
        source = cfg[key]
        for path_key, hash_key in (
            ("path", "sha256"),
            ("manifest_path", "manifest_sha256"),
        ):
            actual = sha256_file(Path(source[path_key]))
            if actual != source[hash_key]:
                raise RuntimeError(f"{key} {path_key} drift")
    oracle = cfg["oracle_source"]
    if sha256_file(PACKAGE_ROOT / oracle["path"]) != oracle["sha256"]:
        raise RuntimeError("Oracle evaluation source drift")
    return checked


def _window_name(timestamp: pd.Timestamp, cfg: dict[str, Any]) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def load_crossasset_source(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = cfg["crossasset_source"]
    frame = pd.read_parquet(Path(source["path"]))
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    frame = (
        frame.drop_duplicates("timestamp_utc", keep="last")
        .sort_values("timestamp_utc")
        .set_index("timestamp_utc")
    )
    required = {
        "dollaridxusd_mid_close",
        "ustbondtrusd_mid_close",
        "dollaridxusd_available",
        "ustbondtrusd_available",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"Missing cross-asset columns: {sorted(missing)}")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if manifest["bars"]["sha256"] != source["sha256"]:
        raise RuntimeError("Cross-asset manifest bar hash drift")
    if manifest["contract_sha256"] != source["contract_sha256"]:
        raise RuntimeError("Cross-asset contract hash drift")
    return frame, {
        "path": source["path"],
        "sha256": source["sha256"],
        "manifest_path": source["manifest_path"],
        "manifest_sha256": source["manifest_sha256"],
        "contract_sha256": source["contract_sha256"],
        "rows": int(len(frame)),
        "first_utc": frame.index.min().isoformat(),
        "last_utc": frame.index.max().isoformat(),
    }


def _completed_market_bar(
    frame: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> pd.Series | None:
    if timestamp not in frame.index:
        return None
    row = frame.loc[timestamp]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[-1]
    available = (
        bool(row["dollaridxusd_available"])
        and bool(row["ustbondtrusd_available"])
    )
    if not available:
        return None
    if pd.isna(row["dollaridxusd_mid_close"]) or pd.isna(
        row["ustbondtrusd_mid_close"]
    ):
        return None
    return row


def _state_join(
    candidates: pd.DataFrame,
    state: pd.DataFrame,
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
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
    ordered = candidates.sort_values("state_time_utc").copy()
    ordered["state_time_utc"] = ordered["state_time_utc"].dt.as_unit(
        "ns"
    )
    return pd.merge_asof(
        ordered,
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )


def build_candidates(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    crossasset: pd.DataFrame,
    events: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    bars = int(strategy["completed_observation_bars"])
    if bars != 3 or int(strategy["observation_minutes"]) != 15:
        raise RuntimeError("Frozen rule requires three completed M5 bars")
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    buffer = float(strategy["stop_buffer_pips"]) * PIP
    floor_pips = float(strategy["stop_floor_pips"])
    ceiling_pips = float(strategy["stop_ceiling_pips"])
    start_bound = min(
        pd.Timestamp(value[0]) for value in cfg["windows"].values()
    )
    end_bound = max(
        pd.Timestamp(value[1]) for value in cfg["windows"].values()
    )
    filtered = events[
        events["currency"].eq(strategy["event_currency"])
    ].copy()
    filtered["event_time_utc"] = pd.to_datetime(
        filtered["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    clusters = (
        filtered[
            filtered["event_time_utc"].between(
                start_bound, end_bound, inclusive="both"
            )
        ]
        .groupby("event_time_utc", sort=True)
    )
    records: list[dict[str, Any]] = []
    reasons = {
        "clusters_in_frozen_period": int(clusters.ngroups),
        "entry_outside_eurusd": 0,
        "eurusd_observation_missing": 0,
        "crossasset_baseline_or_endpoint_missing": 0,
        "same_direction_or_zero_reaction": 0,
        "risk_ceiling": 0,
        "quarantine": 0,
    }
    quarantine = load_ensemble_config()["quarantine"]
    for event_time, cluster in clusters:
        event_time = pd.Timestamp(event_time)
        observation_start = event_time.floor("5min")
        expected = pd.date_range(
            observation_start, periods=bars, freq="5min"
        )
        entry_time = observation_start + pd.Timedelta(minutes=15)
        pre_time = observation_start - pd.Timedelta(minutes=5)
        endpoint_time = expected[-1]
        if entry_time not in eurusd.index:
            reasons["entry_outside_eurusd"] += 1
            continue
        if any(timestamp not in eurusd.index for timestamp in expected):
            reasons["eurusd_observation_missing"] += 1
            continue
        before = _completed_market_bar(crossasset, pre_time)
        after = _completed_market_bar(crossasset, endpoint_time)
        if before is None or after is None:
            reasons["crossasset_baseline_or_endpoint_missing"] += 1
            continue
        dxy_reaction = float(
            after["dollaridxusd_mid_close"]
            - before["dollaridxusd_mid_close"]
        )
        bond_reaction = float(
            after["ustbondtrusd_mid_close"]
            - before["ustbondtrusd_mid_close"]
        )
        if dxy_reaction > 0 and bond_reaction < 0:
            side = "SHORT"
        elif dxy_reaction < 0 and bond_reaction > 0:
            side = "LONG"
        else:
            reasons["same_direction_or_zero_reaction"] += 1
            continue
        if is_quarantined(entry_time, "EURUSD", quarantine):
            reasons["quarantine"] += 1
            continue
        position = int(eurusd.index.get_loc(entry_time))
        entry_bar = eurusd.iloc[position]
        observation = eurusd.loc[expected]
        if side == "LONG":
            entry = _effective_ask(entry_bar, "open", spread_floor)
            entry += slippage
            structure_stop = (
                float(observation["bid_low"].min()) - buffer
            )
            risk_pips = max(
                (entry - structure_stop) / PIP, floor_pips
            )
            stop = entry - risk_pips * PIP
            target = (
                entry
                + float(strategy["target_r"]) * risk_pips * PIP
            )
        else:
            entry = float(entry_bar["bid_open"]) - slippage
            structure_stop = (
                max(
                    _effective_ask(row, "high", spread_floor)
                    for _, row in observation.iterrows()
                )
                + buffer
            )
            risk_pips = max(
                (structure_stop - entry) / PIP, floor_pips
            )
            stop = entry + risk_pips * PIP
            target = (
                entry
                - float(strategy["target_r"]) * risk_pips * PIP
            )
        if risk_pips > ceiling_pips:
            reasons["risk_ceiling"] += 1
            continue
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "event_time_utc": event_time,
                "event_cluster_size": int(len(cluster)),
                "event_ids": "|".join(
                    cluster["event_id"].astype(str)
                ),
                "event_tags": "|".join(
                    cluster["tag"].fillna("").astype(str)
                ),
                "event_titles": " | ".join(
                    cluster["title"].fillna("").astype(str)
                ),
                "pre_event_bar_utc": pre_time,
                "observation_start_utc": observation_start,
                "observation_endpoint_utc": endpoint_time,
                "entry_time_utc": entry_time,
                "entry_position": position,
                "state_time_utc": (
                    entry_time.floor("h") - pd.Timedelta(hours=1)
                ),
                "side": side,
                "dxy_reaction": dxy_reaction,
                "bond_reaction": bond_reaction,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "risk_pips": risk_pips,
                "risk_distance": risk_pips * PIP,
                "window": _window_name(entry_time, cfg),
                "eligible_date": entry_time.strftime("%Y-%m-%d"),
            }
        )
    raw = pd.DataFrame(records)
    joined = _state_join(raw, state)
    if joined.empty:
        candidates = joined
        regime_rejected = 0
    else:
        neutral = (
            joined["direction"].eq("NEUTRAL")
            & ~joined["shock"].astype("boolean").fillna(True)
            & ~(
                joined["DXY_compressed"]
                .astype("boolean")
                .fillna(False)
                & joined["EURUSD_compressed"]
                .astype("boolean")
                .fillna(False)
            )
        )
        regime_rejected = int((~neutral).sum())
        candidates = joined[neutral].copy()
    candidates = candidates.sort_values(
        ["entry_time_utc", "event_ids"]
    ).reset_index(drop=True)
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    census = {
        "qualifying_usd_event_rows": int(len(filtered)),
        "qualifying_usd_event_clusters": int(clusters.ngroups),
        "agreement_candidates_before_regime": int(len(raw)),
        "non_neutral_or_other_regime_rejections": regime_rejected,
        "neutral_candidates": int(len(candidates)),
        "neutral_by_window": by_window,
        "neutral_by_side": by_side,
        "candidate_days": (
            int(candidates["eligible_date"].nunique())
            if not candidates.empty
            else 0
        ),
        "cash_reasons": reasons,
    }
    gate = cfg["outcome_blind_census"]
    forward_full = ("chronological_2023", "chronological_2024", "chronological_2025")
    checks = {
        "total": (
            census["neutral_candidates"]
            >= int(gate["minimum_candidates_total"])
        ),
        "development": (
            by_window["development_2019_2022"]
            >= int(gate["minimum_candidates_development"])
        ),
        "full_forward_years": all(
            by_window[name]
            >= int(gate["minimum_candidates_each_full_forward_year"])
            for name in forward_full
        ),
        "recent_half_year": (
            by_window["recent_2026_h1"]
            >= int(gate["minimum_candidates_recent_half_year"])
        ),
        "both_sides": all(
            by_side[side] >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
    }
    census["gate_results"] = checks
    census["passed"] = bool(all(checks.values()))
    return candidates, census


def execute(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    hold = pd.Timedelta(
        hours=float(strategy["maximum_hold_hours"])
    )
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    skipped_open = 0
    for _, candidate in candidates.sort_values(
        ["entry_time_utc", "event_ids"]
    ).iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time <= open_until:
            skipped_open += 1
            continue
        position = int(candidate["entry_position"])
        side = str(candidate["side"])
        entry = float(candidate["entry_price"])
        stop = float(candidate["stop_price"])
        target = float(candidate["target_price"])
        risk = float(candidate["risk_distance"])
        risk_pips = float(candidate["risk_pips"])
        exit_time, exit_price, reason = _walk_exit(
            eurusd,
            position,
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        signed_move = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        outcome_r = signed_move / risk
        stressed_r = (
            outcome_r
            - float(execution["extra_round_trip_stress_pips"])
            / risk_pips
        )
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "window": candidate["window"],
                "eligible_date": candidate["eligible_date"],
                "event_time_utc": candidate["event_time_utc"],
                "event_ids": candidate["event_ids"],
                "event_titles": candidate["event_titles"],
                "side": side,
                "dxy_reaction": candidate["dxy_reaction"],
                "bond_reaction": candidate["bond_reaction"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "risk_pips": risk_pips,
                "r": outcome_r,
                "extra_half_pip_stress_r": stressed_r,
                "fixed_0p01_lot_usd": (
                    signed_move / PIP * 0.10
                ),
            }
        )
        open_until = exit_time
    return pd.DataFrame(records), {
        "candidate_signals": int(len(candidates)),
        "executed_trades": int(len(records)),
        "skipped_while_position_open": skipped_open,
    }


def _top_removed(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    remove = int(math.ceil(len(trades) * 0.05))
    return trades.sort_values("r").iloc[:-remove].copy()


def summarize(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    overall = payoff_metrics(trades)
    windows = {
        name: payoff_metrics(trades[trades["window"].eq(name)])
        for name in cfg["windows"]
    }
    sides = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(_top_removed(trades))
    oracle, matches = oracle_metrics(trades)
    recent = trades[trades["window"].eq("recent_2026_h1")].copy()
    if recent.empty:
        recent_monthly: dict[str, Any] = {}
    else:
        recent["month"] = recent["entry_time_utc"].dt.strftime("%Y-%m")
        recent_monthly = {
            str(month): payoff_metrics(group)
            for month, group in recent.groupby("month", sort=True)
        }
    gate = cfg["admission"]
    checks = {
        "total_trades": (
            overall["trades"]
            >= int(gate["minimum_executed_trades_total"])
        ),
        "development_sample": (
            windows["development_2019_2022"]["trades"]
            >= int(gate["minimum_executed_trades_development"])
        ),
        "forward_samples": (
            all(
                windows[name]["trades"]
                >= int(
                    gate[
                        "minimum_executed_trades_each_full_forward_year"
                    ]
                )
                for name in (
                    "chronological_2023",
                    "chronological_2024",
                    "chronological_2025",
                )
            )
            and windows["recent_2026_h1"]["trades"]
            >= int(gate["minimum_executed_trades_recent_half_year"])
        ),
        "win_rate": (
            float(gate["minimum_overall_win_rate"])
            <= overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "payoff": (
            float(gate["minimum_overall_realized_payoff_ratio"])
            <= overall["realized_payoff_ratio"]
            <= float(gate["maximum_overall_realized_payoff_ratio"])
        ),
        "overall_profit_factor": (
            overall["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "every_window_profitable": all(
            value["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            for value in windows.values()
        ),
        "both_sides": all(
            sides[side]["trades"]
            >= int(gate["minimum_each_side_trades"])
            and sides[side]["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "drawdown": (
            overall["max_drawdown_r"]
            <= float(gate["maximum_drawdown_r"])
        ),
        "top_winner_removal": (
            top_removed["profit_factor"]
            >= float(gate["minimum_top_5pct_removed_profit_factor"])
        ),
        "extra_half_pip": (
            stressed["profit_factor"]
            >= float(gate["minimum_extra_half_pip_profit_factor"])
        ),
        "oracle_precision": (
            oracle["same_side_15m_precision"]
            >= float(
                gate["minimum_same_side_15m_oracle_precision"]
            )
        ),
        "oracle_recall": (
            oracle["same_side_15m_recall"]
            >= float(gate["minimum_same_side_15m_oracle_recall"])
        ),
    }
    return (
        {
            "overall": overall,
            "windows": windows,
            "by_side": sides,
            "recent_2026_h1_monthly": recent_monthly,
            "top_5pct_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "oracle_resemblance": oracle,
            "fixed_0p01_lot_usd": {
                "net": float(trades["fixed_0p01_lot_usd"].sum()),
                "recent_2026_h1": float(
                    recent["fixed_0p01_lot_usd"].sum()
                ),
            },
            "gate_results": checks,
            "passed": bool(all(checks.values())),
        },
        matches,
    )


def _load_all() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    cfg = load_config()
    base = load_ensemble_config()
    eurusd, state, manifests = load_inputs(base)
    crossasset, crossasset_manifest = load_crossasset_source(cfg)
    event_cfg = load_event_config()
    events = qualifying_events(load_event_source(event_cfg), event_cfg)
    source_manifest = {
        **manifests,
        "CROSSASSET_M5": crossasset_manifest,
        "EVENTS": {
            "path": cfg["event_source"]["path"],
            "sha256": cfg["event_source"]["sha256"],
            "manifest_path": cfg["event_source"]["manifest_path"],
            "manifest_sha256": cfg["event_source"]["manifest_sha256"],
            "qualifying_rows_all_currencies": int(len(events)),
        },
    }
    return cfg, eurusd, state, crossasset, events, source_manifest


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg, eurusd, state, crossasset, events, manifests = _load_all()
    candidates, census = build_candidates(
        eurusd, state, crossasset, events, cfg
    )
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_event_crossasset_rates_census_v1"
                ),
                "family": FAMILY,
                "status": (
                    "CENSUS_PASS_BACKTEST_ALLOWED"
                    if census["passed"]
                    else "CENSUS_FAIL_NO_PNL_ALLOWED"
                ),
                "census": census,
                "data_manifests": manifests,
            }
        ),
        candidates,
    )


def run_backtest() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg, eurusd, state, crossasset, events, manifests = _load_all()
    candidates, census = build_candidates(
        eurusd, state, crossasset, events, cfg
    )
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades, execution = execute(candidates, eurusd, cfg)
    summary, matches = summarize(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_EVENT_CROSSASSET_RATES_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_event_crossasset_rates_result_v1"
        ),
        "family": FAMILY,
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "information_status": cfg["information_status"],
        "research_boundary": (
            "All archived windows are adaptive historical development data. "
            "Chronological labels do not make them pristine holdouts."
        ),
        "mechanism": (
            "Qualifying USD event plus completed DXY/Treasury opposite-sign "
            "reaction, routed only in the causal Neutral regime."
        ),
        "census": census,
        "execution": execution,
        "summary": summary,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates,
            "TRADES": trades,
            "ORACLE_MATCHES_15M": matches,
        },
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "OUTPUT_ROOT",
    "build_candidates",
    "execute",
    "load_config",
    "load_crossasset_source",
    "run_backtest",
    "run_census",
    "summarize",
    "verify_lock",
    "write_json",
]
