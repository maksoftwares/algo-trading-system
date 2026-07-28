from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_symmetric_rsi_1p5r import (
    _effective_ask,
    _walk_exit,
    load_oracle,
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


FAMILY = "N36_NEUTRAL_BLS_RELEASE_ACCELERATION"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_bls_release_acceleration"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_bls_release_acceleration.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_BLS_RELEASE_ACCELERATION_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("BLS acceleration contract is not outcome-locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"BLS acceleration preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in ("data_and_classifier_contract", "source_audit"):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    source = cfg["initial_release_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("BLS normalized source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("BLS source manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if manifest["raw_pdf_chain_sha256"] != source["raw_pdf_chain_sha256"]:
        raise RuntimeError("BLS raw PDF chain drift")
    oracle = cfg["oracle_source"]
    if sha256_file(PACKAGE_ROOT / oracle["path"]) != oracle["sha256"]:
        raise RuntimeError("Oracle evaluation source drift")
    return checked


def _window_name(timestamp: pd.Timestamp, cfg: dict[str, Any]) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def load_release_source(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = cfg["initial_release_source"]
    frame = pd.read_parquet(Path(source["path"]))
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    frame = frame.sort_values(
        ["family", "event_time_utc"]
    ).reset_index(drop=True)
    required = {
        "family",
        "event_time_utc",
        "initial_value",
        "source_pdf_sha256",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"Missing BLS columns: {sorted(missing)}")
    if frame.duplicated(["family", "event_time_utc"]).any():
        raise RuntimeError("Duplicate BLS family/release timestamp")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    return frame, {
        "path": source["path"],
        "sha256": source["sha256"],
        "manifest_path": source["manifest_path"],
        "manifest_sha256": source["manifest_sha256"],
        "raw_pdf_chain_sha256": source["raw_pdf_chain_sha256"],
        "rows": int(len(frame)),
        "first_utc": frame["event_time_utc"].min().isoformat(),
        "last_utc": frame["event_time_utc"].max().isoformat(),
        "coverage_by_family": manifest["coverage_by_family"],
        "parse_errors": len(manifest["parse_errors"]),
    }


def build_release_signals(
    releases: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    strategy = cfg["strategy"]
    frame = releases[
        releases["family"].isin(strategy["families"])
    ].sort_values(["family", "event_time_utc"]).copy()
    frame["previous_event_time_utc"] = frame.groupby(
        "family"
    )["event_time_utc"].shift(1)
    frame["previous_initial_value"] = frame.groupby(
        "family"
    )["initial_value"].shift(1)
    frame["predecessor_days"] = (
        frame["event_time_utc"]
        - frame["previous_event_time_utc"]
    ).dt.total_seconds() / 86_400.0
    interval = frame["predecessor_days"].between(
        float(strategy["minimum_predecessor_calendar_days"]),
        float(strategy["maximum_predecessor_calendar_days"]),
        inclusive="both",
    )
    frame["acceleration"] = (
        frame["initial_value"] - frame["previous_initial_value"]
    )
    nonzero = frame["acceleration"].ne(0) & frame["acceleration"].notna()
    selected = frame[interval & nonzero].copy()
    selected["side"] = "LONG"
    selected.loc[selected["acceleration"].gt(0), "side"] = "SHORT"
    return selected.reset_index(drop=True), {
        "source_rows": int(len(frame)),
        "missing_or_out_of_interval_predecessor": int((~interval).sum()),
        "zero_acceleration": int((interval & ~nonzero).sum()),
        "directional_release_signals": int(len(selected)),
    }


def _state_join(
    signals: pd.DataFrame,
    state: pd.DataFrame,
) -> pd.DataFrame:
    if signals.empty:
        return signals.copy()
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
    ordered = signals.sort_values("state_time_utc").copy()
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
    releases: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    signals, source_census = build_release_signals(releases, cfg)
    signals = signals.rename(columns={"family": "macro_family"})
    wait = int(cfg["strategy"]["observation_wait_minutes"])
    signals["entry_time_utc"] = (
        signals["event_time_utc"].dt.floor("5min")
        + pd.Timedelta(minutes=wait)
    )
    signals["state_time_utc"] = (
        signals["entry_time_utc"].dt.floor("h")
        - pd.Timedelta(hours=1)
    )
    in_archive = signals["entry_time_utc"].isin(eurusd.index)
    missing_entry = int((~in_archive).sum())
    signals = signals[in_archive].copy()
    quarantine = load_ensemble_config()["quarantine"]
    quarantined = signals["entry_time_utc"].map(
        lambda value: is_quarantined(
            value, "EURUSD", quarantine
        )
    )
    quarantine_count = int(quarantined.sum())
    signals = signals[~quarantined].copy()
    joined = _state_join(signals, state)
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
    candidates["family"] = FAMILY
    candidates["regime"] = "NEUTRAL"
    candidates["window"] = candidates["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    candidates["eligible_date"] = candidates[
        "entry_time_utc"
    ].dt.strftime("%Y-%m-%d")
    candidates["entry_position"] = candidates["entry_time_utc"].map(
        lambda value: int(eurusd.index.get_loc(value))
    )
    candidates = candidates.sort_values(
        ["entry_time_utc", "macro_family"]
    ).reset_index(drop=True)
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    by_family = {
        family: int(candidates["macro_family"].eq(family).sum())
        for family in cfg["strategy"]["families"]
    }
    census = {
        **source_census,
        "missing_eurusd_entry": missing_entry,
        "quarantined": quarantine_count,
        "non_neutral_or_other_regime_rejections": regime_rejected,
        "neutral_candidates": int(len(candidates)),
        "neutral_by_window": by_window,
        "neutral_by_side": by_side,
        "neutral_by_macro_family": by_family,
        "candidate_days": (
            int(candidates["eligible_date"].nunique())
            if not candidates.empty
            else 0
        ),
    }
    gate = cfg["outcome_blind_census"]
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
            for name in (
                "chronological_2023",
                "chronological_2024",
                "chronological_2025",
            )
        ),
        "recent_half_year": (
            by_window["recent_2026_h1"]
            >= int(gate["minimum_candidates_recent_half_year"])
        ),
        "both_sides": all(
            by_side[side] >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "families": (
            sum(value > 0 for value in by_family.values())
            >= int(gate["minimum_families_represented"])
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
    risk = float(strategy["stop_pips"]) * PIP
    target_distance = float(strategy["target_r"]) * risk
    hold = pd.Timedelta(
        hours=float(strategy["maximum_hold_hours"])
    )
    records: list[dict[str, Any]] = []
    skipped_open = 0
    open_until: pd.Timestamp | None = None
    for _, candidate in candidates.sort_values(
        ["entry_time_utc", "macro_family"]
    ).iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time <= open_until:
            skipped_open += 1
            continue
        position = int(candidate["entry_position"])
        bar = eurusd.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = _effective_ask(bar, "open", spread_floor) + slippage
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
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
        stress_r = (
            outcome_r
            - float(execution["extra_round_trip_stress_pips"])
            / float(strategy["stop_pips"])
        )
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "macro_family": candidate["macro_family"],
                "window": candidate["window"],
                "eligible_date": candidate["eligible_date"],
                "event_time_utc": candidate["event_time_utc"],
                "initial_value": candidate["initial_value"],
                "previous_initial_value": candidate[
                    "previous_initial_value"
                ],
                "acceleration": candidate["acceleration"],
                "side": side,
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "risk_pips": float(strategy["stop_pips"]),
                "r": outcome_r,
                "extra_half_pip_stress_r": stress_r,
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


def same_day_oracle_metrics(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    oracle = load_oracle()
    oracle_keys = set(
        zip(
            oracle["entry_time_utc"].dt.strftime("%Y-%m-%d"),
            oracle["side"],
            strict=False,
        )
    )
    matches = [
        (
            timestamp.strftime("%Y-%m-%d"),
            side,
        )
        in oracle_keys
        for timestamp, side in zip(
            trades["entry_time_utc"],
            trades["side"],
            strict=False,
        )
    ]
    return {
        "trades": int(len(trades)),
        "same_day_same_side_matches": int(sum(matches)),
        "same_day_same_side_precision": (
            float(sum(matches) / len(trades)) if len(trades) else 0.0
        ),
    }


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
    families = {
        family: payoff_metrics(
            trades[trades["macro_family"].eq(family)]
        )
        for family in cfg["strategy"]["families"]
    }
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(_top_removed(trades))
    oracle_clock, matches = oracle_metrics(trades)
    oracle_day = same_day_oracle_metrics(trades)
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
        "oracle_day_precision": (
            oracle_day["same_day_same_side_precision"]
            >= float(
                gate["minimum_same_day_same_side_oracle_precision"]
            )
        ),
    }
    return (
        {
            "overall": overall,
            "windows": windows,
            "by_side": sides,
            "by_macro_family": families,
            "recent_2026_h1_monthly": recent_monthly,
            "top_5pct_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "oracle_clock_resemblance": oracle_clock,
            "oracle_same_day_resemblance": oracle_day,
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
    dict[str, Any],
]:
    cfg = load_config()
    eurusd, state, manifests = load_inputs(load_ensemble_config())
    releases, release_manifest = load_release_source(cfg)
    return (
        cfg,
        eurusd,
        state,
        releases,
        {**manifests, "BLS_INITIAL_RELEASES": release_manifest},
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg, eurusd, state, releases, manifests = _load_all()
    candidates, census = build_candidates(
        eurusd, state, releases, cfg
    )
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_bls_release_acceleration_census_v1"
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
    cfg, eurusd, state, releases, manifests = _load_all()
    candidates, census = build_candidates(
        eurusd, state, releases, cfg
    )
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades, execution = execute(candidates, eurusd, cfg)
    summary, matches = summarize(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_BLS_RELEASE_ACCELERATION_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_bls_release_acceleration_result_v1"
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
            "Current first-published BLS headline minus prior same-family "
            "first-published headline, followed by a 15-minute wait and "
            "causal Neutral regime ownership."
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
    "build_release_signals",
    "execute",
    "load_config",
    "load_release_source",
    "run_backtest",
    "run_census",
    "summarize",
    "verify_lock",
    "write_json",
]
