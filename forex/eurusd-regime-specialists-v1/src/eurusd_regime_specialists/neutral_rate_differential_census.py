from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_rate_differential_census.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_RATE_DIFFERENTIAL_CENSUS_V1_1_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_rate_differential_census"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_candidate_count") is not True
        or lock.get("eurusd_outcome_use_allowed") is not False
        or lock.get("parameter_search_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Rate-differential census lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Rate-differential census drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def load_official_rates(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest = config["source_manifest"]
    audit = config["source_audit"]
    if sha256_file(Path(manifest["path"])) != manifest["sha256"]:
        raise RuntimeError("Official source manifest drift")
    if sha256_file(Path(audit["path"])) != audit["sha256"]:
        raise RuntimeError("Official source audit drift")
    audit_data = json.loads(Path(audit["path"]).read_text(encoding="utf-8"))
    if audit_data["status"] != audit["required_status"]:
        raise RuntimeError("Official rate source is not accepted")
    sources = config["normalized_sources"]
    frames: dict[str, pd.DataFrame] = {}
    for name, source in sources.items():
        path = Path(source["path"])
        if sha256_file(path) != source["sha256"]:
            raise RuntimeError(f"Official normalized source drift: {name}")
        frame = pd.read_csv(path)
        frame["observation_date"] = pd.to_datetime(
            frame["observation_date"], errors="raise"
        ).dt.normalize()
        if frame["observation_date"].duplicated().any():
            raise RuntimeError(f"Duplicate official dates: {name}")
        frames[name] = frame.sort_values("observation_date").reset_index(
            drop=True
        )
    return (
        frames["us_treasury_2y"],
        frames["ecb_euro_area_aaa_2y"],
    )


def build_common_curve(
    treasury: pd.DataFrame, ecb: pd.DataFrame
) -> pd.DataFrame:
    common = treasury.merge(ecb, on="observation_date", how="inner")
    common["spread_percent"] = (
        common["us_treasury_2y_percent"]
        - common["ecb_euro_area_aaa_2y_percent"]
    )
    common["spread_change_bps"] = common["spread_percent"].diff() * 100.0
    return common.sort_values("observation_date").reset_index(drop=True)


def load_neutral_midnights(config: dict[str, Any]) -> pd.DataFrame:
    source = config["neutral_timestamp_source"]
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Neutral timestamp source drift")
    frame = pd.read_parquet(path, columns=source["columns_allowed"])
    frame["entry_time_utc"] = pd.to_datetime(
        frame["entry_time_utc"], utc=True, errors="raise"
    )
    clock = source["required_clock_utc"]
    selected = frame[
        frame["entry_time_utc"].dt.strftime("%H:%M").eq(clock)
    ].copy()
    required_sides = set(source["required_side_rows_per_clock"])
    valid_times = []
    for entry_time, block in selected.groupby("entry_time_utc", sort=True):
        if set(block["side"]) != required_sides or len(block) != len(
            required_sides
        ):
            raise RuntimeError("Neutral midnight side-pair drift")
        valid_times.append(entry_time)
    result = pd.DataFrame({"entry_time_utc": valid_times})
    if result["entry_time_utc"].duplicated().any():
        raise RuntimeError("Duplicate Neutral midnight timestamps")
    return result


def _window_name(entry: pd.Timestamp, config: dict[str, Any]) -> str:
    for name, bounds in config["windows"].items():
        start, end = (pd.Timestamp(value) for value in bounds)
        if start <= entry <= end:
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def build_candidates(
    neutral_midnights: pd.DataFrame,
    common_curve: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    signal = config["signal"]
    lag_days = int(signal["minimum_observation_lag_calendar_days"])
    threshold = float(
        signal["minimum_absolute_common_date_spread_change_bps_inclusive"]
    )
    records: list[dict[str, Any]] = []
    insufficient_history = 0
    subthreshold = 0
    for entry_time in neutral_midnights["entry_time_utc"]:
        cutoff = (entry_time - pd.Timedelta(days=lag_days)).tz_localize(
            None
        ).normalize()
        available = common_curve[
            common_curve["observation_date"].le(cutoff)
        ]
        if len(available) < 2:
            insufficient_history += 1
            continue
        current = available.iloc[-1]
        change_bps = float(current["spread_change_bps"])
        if not np.isfinite(change_bps) or abs(change_bps) < threshold:
            subthreshold += 1
            continue
        side = (
            signal["widening_spread_side"]
            if change_bps > 0.0
            else signal["narrowing_spread_side"]
        )
        observation_date = pd.Timestamp(current["observation_date"])
        lag = (entry_time.tz_localize(None).normalize() - observation_date).days
        if lag < lag_days:
            raise RuntimeError("Rate observation availability violation")
        records.append(
            {
                "entry_time_utc": entry_time,
                "eligible_date": entry_time.strftime("%Y-%m-%d"),
                "side": side,
                "observation_date": observation_date.strftime("%Y-%m-%d"),
                "observation_lag_calendar_days": lag,
                "us_treasury_2y_percent": float(
                    current["us_treasury_2y_percent"]
                ),
                "ecb_euro_area_aaa_2y_percent": float(
                    current["ecb_euro_area_aaa_2y_percent"]
                ),
                "spread_percent": float(current["spread_percent"]),
                "spread_change_bps": change_bps,
                "window": _window_name(entry_time, config),
            }
        )
    candidates = pd.DataFrame(records)
    if not candidates.empty:
        candidates = candidates.sort_values("entry_time_utc").reset_index(
            drop=True
        )
    counts_by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in config["windows"]
    }
    counts_by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    gates = config["capacity_gates"]
    gate_results = {
        "minimum_total_candidates": len(candidates)
        >= int(gates["minimum_total_candidates"]),
        "minimum_development_candidates": counts_by_window[
            "DEVELOPMENT_2019_2022"
        ]
        >= int(gates["minimum_development_candidates"]),
        "minimum_each_full_oos_year": all(
            counts_by_window[name]
            >= int(gates["minimum_candidates_each_full_oos_year"])
            for name in ("OOS_2023", "OOS_2024", "OOS_2025")
        ),
        "minimum_2026_h1": counts_by_window["OOS_2026_H1"]
        >= int(gates["minimum_candidates_2026_h1"]),
        "minimum_each_side": all(
            counts_by_side[side] >= int(gates["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
    }
    census = {
        "schema_version": "eurusd_neutral_rate_differential_census_result_v1",
        "status": (
            "CENSUS_PASS_EXECUTION_FREEZE_ALLOWED"
            if all(gate_results.values())
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "neutral_midnight_timestamps": len(neutral_midnights),
        "common_rate_observation_dates": len(common_curve),
        "insufficient_history_cash": insufficient_history,
        "subthreshold_cash": subthreshold,
        "candidates": len(candidates),
        "candidates_by_window": counts_by_window,
        "candidates_by_side": counts_by_side,
        "minimum_observation_lag_calendar_days_observed": (
            int(candidates["observation_lag_calendar_days"].min())
            if not candidates.empty
            else None
        ),
        "gate_results": gate_results,
        "all_capacity_gates_passed": all(gate_results.values()),
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "broker_action_allowed": False,
    }
    return candidates, census


def run_census() -> dict[str, Any]:
    verify_lock()
    config = load_config()
    treasury, ecb = load_official_rates(config)
    common = build_common_curve(treasury, ecb)
    neutral = load_neutral_midnights(config)
    candidates, census = build_candidates(neutral, common, config)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(
        OUTPUT_ROOT / "CANDIDATES.csv",
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S.%fZ",
    )
    (OUTPUT_ROOT / "CENSUS.json").write_text(
        json.dumps(census, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return census
