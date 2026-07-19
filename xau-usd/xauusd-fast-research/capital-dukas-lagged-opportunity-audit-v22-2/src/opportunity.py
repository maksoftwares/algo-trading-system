from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_dukas_lagged_opportunity_audit_v22_2.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: dict[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(REPO.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def verify_upstream(config: dict[str, Any], root: Path = ROOT) -> None:
    upstream = config["upstream"]
    checks = (
        ("paired_quotes", "paired_quotes_sha256"),
        ("foundation_contract", "foundation_contract_sha256"),
        ("timing_limitation", "timing_limitation_sha256"),
    )
    for path_key, hash_key in checks:
        path = resolve(root, str(upstream[path_key]))
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != str(upstream[hash_key]):
            raise ValueError(f"V22.2 upstream hash changed: {path}")


def load_paired_quotes(config: dict[str, Any], root: Path = ROOT) -> pd.DataFrame:
    verify_upstream(config, root)
    path = resolve(root, str(config["upstream"]["paired_quotes"]))
    columns = [
        "timestamp_utc",
        "capital_timestamp_ms",
        "capital_bid",
        "capital_ask",
        "capital_mid",
        "capital_spread",
        "dukas_timestamp_ms",
        "dukas_mid",
    ]
    frame = pd.read_parquet(path, columns=columns)
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True, errors="raise"
    )
    numeric = [column for column in columns if column != "timestamp_utc"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame = frame.sort_values("capital_timestamp_ms", kind="mergesort")
    if frame["capital_timestamp_ms"].duplicated().any():
        raise ValueError("V22.2 upstream Capital timestamps are duplicated")
    if not frame["dukas_timestamp_ms"].le(frame["capital_timestamp_ms"]).all():
        raise ValueError("V22.2 upstream contains a future Dukascopy match")
    if np.any(frame["capital_ask"] < frame["capital_bid"]):
        raise ValueError("V22.2 upstream contains a crossed Capital quote")
    return frame.reset_index(drop=True)


def _safe_snapshots(
    paired: pd.DataFrame,
    query_ms: np.ndarray,
    maximum_delay_ms: int,
    prefix: str,
) -> pd.DataFrame:
    left = pd.DataFrame(
        {
            "row_id": np.arange(len(paired), dtype=np.int64),
            "query_ms": np.asarray(query_ms, dtype=np.int64),
        }
    ).sort_values("query_ms", kind="mergesort")
    right = paired[
        ["capital_timestamp_ms", "dukas_timestamp_ms", "dukas_mid"]
    ].rename(
        columns={
            "capital_timestamp_ms": "source_capital_timestamp_ms",
            "dukas_timestamp_ms": "source_dukas_timestamp_ms",
            "dukas_mid": "source_dukas_mid",
        }
    )
    right = right.sort_values("source_capital_timestamp_ms", kind="mergesort")
    matched = pd.merge_asof(
        left,
        right,
        left_on="query_ms",
        right_on="source_capital_timestamp_ms",
        direction="backward",
        tolerance=int(maximum_delay_ms),
        allow_exact_matches=True,
    ).sort_values("row_id", kind="mergesort")
    delay = matched["query_ms"] - matched["source_capital_timestamp_ms"]
    if delay.dropna().lt(0).any():
        raise ValueError("V22.2 safe snapshot matched forward")
    return pd.DataFrame(
        {
            f"{prefix}_query_ms": matched["query_ms"].to_numpy(),
            f"{prefix}_source_capital_timestamp_ms": matched[
                "source_capital_timestamp_ms"
            ].to_numpy(),
            f"{prefix}_dukas_timestamp_ms": matched[
                "source_dukas_timestamp_ms"
            ].to_numpy(),
            f"{prefix}_dukas_mid": matched["source_dukas_mid"].to_numpy(),
            f"{prefix}_snapshot_delay_ms": delay.to_numpy(),
        }
    )


def _add_trailing_basis_statistics(
    features: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    feature_config = config["feature"]
    reset_ms = int(feature_config["gap_reset_minutes"]) * 60_000
    gaps = features["capital_timestamp_ms"].diff().fillna(reset_ms + 1)
    features = features.copy()
    features["segment_id"] = gaps.gt(reset_ms).cumsum().astype(np.int64)
    features["basis_trailing_count"] = np.nan
    features["basis_trailing_median"] = np.nan
    features["basis_trailing_q25"] = np.nan
    features["basis_trailing_q75"] = np.nan
    duration = f"{int(feature_config['baseline_window_minutes'])}min"
    minimum = int(feature_config["baseline_min_observations"])
    for _, group in features.groupby("segment_id", sort=False):
        time_index = pd.to_datetime(
            group["capital_timestamp_ms"], unit="ms", utc=True
        )
        basis = pd.Series(group["lagged_basis"].to_numpy(), index=time_index)
        rolling = basis.rolling(duration, min_periods=minimum, closed="left")
        features.loc[group.index, "basis_trailing_count"] = (
            rolling.count().to_numpy()
        )
        features.loc[group.index, "basis_trailing_median"] = (
            rolling.median().to_numpy()
        )
        features.loc[group.index, "basis_trailing_q25"] = (
            rolling.quantile(0.25).to_numpy()
        )
        features.loc[group.index, "basis_trailing_q75"] = (
            rolling.quantile(0.75).to_numpy()
        )
    return features


def build_causal_features(
    paired: pd.DataFrame, config: dict[str, Any], safety_lag_ms: int
) -> pd.DataFrame:
    feature_config = config["feature"]
    timestamps = paired["capital_timestamp_ms"].to_numpy(dtype=np.int64)
    safe_query = timestamps - int(safety_lag_ms)
    impulse_query = safe_query - int(feature_config["impulse_lookback_ms"])
    maximum_delay = int(
        config["data_quality"]["maximum_safe_snapshot_delay_ms"]
    )
    safe = _safe_snapshots(paired, safe_query, maximum_delay, "safe")
    impulse_start = _safe_snapshots(
        paired, impulse_query, maximum_delay, "impulse_start"
    )
    features = pd.concat(
        [paired.reset_index(drop=True), safe, impulse_start], axis=1
    )
    features["safety_lag_ms"] = int(safety_lag_ms)
    features["lagged_basis"] = (
        features["capital_mid"] - features["safe_dukas_mid"]
    )
    features["dukas_impulse"] = (
        features["safe_dukas_mid"] - features["impulse_start_dukas_mid"]
    )
    features = _add_trailing_basis_statistics(features, config)
    interquartile_scale = (
        features["basis_trailing_q75"] - features["basis_trailing_q25"]
    ) / 1.349
    features["basis_robust_scale"] = interquartile_scale.clip(
        lower=float(feature_config["minimum_robust_scale_price"])
    )
    features["fair_value_residual"] = (
        features["basis_trailing_median"] - features["lagged_basis"]
    )
    features["candidate_direction"] = np.sign(
        features["fair_value_residual"]
    ).fillna(0).astype(np.int8)
    features["absolute_residual_z"] = (
        features["fair_value_residual"].abs()
        / features["basis_robust_scale"]
    )
    features["directional_dukas_impulse"] = (
        features["candidate_direction"] * features["dukas_impulse"]
    )
    timestamps_utc = pd.to_datetime(
        features["capital_timestamp_ms"], unit="ms", utc=True
    )
    features["date_utc"] = timestamps_utc.dt.strftime("%Y-%m-%d")
    weekday_gate = timestamps_utc.dt.weekday.lt(5)
    safe_inputs = (
        features["safe_source_capital_timestamp_ms"].le(
            features["safe_query_ms"]
        )
        & features["impulse_start_source_capital_timestamp_ms"].le(
            features["impulse_start_query_ms"]
        )
        & features["safe_dukas_timestamp_ms"].le(features["safe_query_ms"])
        & features["impulse_start_dukas_timestamp_ms"].le(
            features["impulse_start_query_ms"]
        )
    )
    if not bool(config["data_quality"]["weekday_only"]):
        weekday_gate = pd.Series(True, index=features.index)
    features["base_opportunity_gate"] = (
        safe_inputs
        & weekday_gate
        & features["basis_trailing_median"].notna()
        & features["basis_robust_scale"].notna()
        & features["candidate_direction"].ne(0)
        & features["capital_spread"].le(
            float(feature_config["maximum_capital_spread_price"])
        )
        & features["fair_value_residual"].abs().ge(
            features["capital_spread"]
            * float(feature_config["minimum_residual_spread_multiple"])
        )
        & features["directional_dukas_impulse"].ge(
            features["capital_spread"]
            * float(feature_config["minimum_impulse_spread_multiple"])
        )
    )
    return features


def select_candidate_episodes(
    features: pd.DataFrame, z_threshold: float, cooldown_minutes: int
) -> pd.DataFrame:
    ordered = features.sort_values("capital_timestamp_ms", kind="mergesort").copy()
    gate = ordered["base_opportunity_gate"] & ordered["absolute_residual_z"].ge(
        float(z_threshold)
    )
    prior_gate = gate.shift(1, fill_value=False)
    prior_direction = ordered["candidate_direction"].shift(1, fill_value=0)
    starts = gate & (
        ~prior_gate | ordered["candidate_direction"].ne(prior_direction)
    )
    cooldown_ms = int(cooldown_minutes) * 60_000
    accepted: list[int] = []
    last_timestamp: int | None = None
    for index in ordered.index[starts]:
        timestamp = int(ordered.at[index, "capital_timestamp_ms"])
        if last_timestamp is None or timestamp - last_timestamp >= cooldown_ms:
            accepted.append(index)
            last_timestamp = timestamp
    return ordered.loc[accepted].copy().reset_index(drop=True)


def full_weekday_roles(
    paired: pd.DataFrame, config: dict[str, Any]
) -> tuple[list[str], list[str], pd.DataFrame]:
    timestamp = pd.to_datetime(paired["capital_timestamp_ms"], unit="ms", utc=True)
    coverage = pd.DataFrame(
        {
            "date_utc": timestamp.dt.strftime("%Y-%m-%d"),
            "weekday": timestamp.dt.weekday,
        }
    )
    daily = coverage.groupby("date_utc", as_index=False).agg(
        paired_quotes=("date_utc", "size"), weekday=("weekday", "first")
    )
    minimum = int(
        config["data_quality"]["minimum_paired_quotes_per_full_day"]
    )
    daily["is_full_weekday"] = daily["weekday"].lt(5) & daily[
        "paired_quotes"
    ].ge(minimum)
    full_dates = daily.loc[daily["is_full_weekday"], "date_utc"].tolist()
    calibration_count = int(config["data_quality"]["calibration_full_weekdays"])
    if len(full_dates) <= calibration_count:
        raise ValueError("V22.2 has no post-calibration full weekdays")
    calibration = full_dates[:calibration_count]
    validation = full_dates[calibration_count:]
    role = np.select(
        [
            daily["date_utc"].isin(calibration),
            daily["date_utc"].isin(validation),
        ],
        ["CALIBRATION", "VALIDATION"],
        default="INCOMPLETE_OR_NONWEEKDAY",
    )
    daily["frequency_role"] = role
    return calibration, validation, daily


def _event_rate(events: pd.DataFrame, dates: list[str]) -> float:
    if not dates:
        return 0.0
    return float(events["date_utc"].isin(dates).sum() / len(dates))


def _threshold_audit(
    features: pd.DataFrame,
    calibration_dates: list[str],
    validation_dates: list[str],
    config: dict[str, Any],
) -> tuple[pd.DataFrame, float]:
    frequency = config["frequency"]
    rows: list[dict[str, Any]] = []
    for threshold in frequency["z_threshold_grid"]:
        events = select_candidate_episodes(
            features, float(threshold), int(frequency["cooldown_minutes"])
        )
        rows.append(
            {
                "z_threshold": float(threshold),
                "calibration_candidates": int(
                    events["date_utc"].isin(calibration_dates).sum()
                ),
                "calibration_candidates_per_day": _event_rate(
                    events, calibration_dates
                ),
                "validation_candidates": int(
                    events["date_utc"].isin(validation_dates).sum()
                ),
                "validation_candidates_per_day": _event_rate(
                    events, validation_dates
                ),
            }
        )
    audit = pd.DataFrame(rows)
    target = float(frequency["calibration_target_candidates_per_day"])
    selected = min(
        rows,
        key=lambda row: (
            abs(float(row["calibration_candidates_per_day"]) - target),
            -float(row["z_threshold"]),
        ),
    )
    audit["selected_by_frequency_calibration"] = audit["z_threshold"].eq(
        float(selected["z_threshold"])
    )
    return audit, float(selected["z_threshold"])


def _event_output(
    events: pd.DataFrame,
    selected_threshold: float,
    role_by_date: dict[str, str],
    analysis_role: str,
) -> pd.DataFrame:
    output = events.copy()
    output["analysis_role"] = analysis_role
    output["frequency_role"] = output["date_utc"].map(role_by_date).fillna(
        "INCOMPLETE_OR_NONWEEKDAY"
    )
    output["selected_z_threshold"] = float(selected_threshold)
    output["candidate_side"] = np.where(
        output["candidate_direction"].gt(0), "LONG", "SHORT"
    )
    columns = [
        "analysis_role",
        "frequency_role",
        "date_utc",
        "timestamp_utc",
        "capital_timestamp_ms",
        "safety_lag_ms",
        "candidate_side",
        "selected_z_threshold",
        "capital_bid",
        "capital_ask",
        "capital_mid",
        "capital_spread",
        "safe_source_capital_timestamp_ms",
        "safe_dukas_timestamp_ms",
        "safe_dukas_mid",
        "safe_snapshot_delay_ms",
        "impulse_start_source_capital_timestamp_ms",
        "impulse_start_dukas_timestamp_ms",
        "impulse_start_dukas_mid",
        "impulse_start_snapshot_delay_ms",
        "dukas_impulse",
        "lagged_basis",
        "basis_trailing_count",
        "basis_trailing_median",
        "basis_robust_scale",
        "fair_value_residual",
        "absolute_residual_z",
        "directional_dukas_impulse",
    ]
    output = output.loc[:, columns].copy()
    output.insert(
        0,
        "opportunity_id",
        [
            f"V22_2_{int(lag):05d}_{index + 1:06d}"
            for index, lag in enumerate(output["safety_lag_ms"])
        ],
    )
    return output


def run_opportunity_audit(
    paired: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    calibration_dates, validation_dates, coverage = full_weekday_roles(
        paired, config
    )
    primary_lag = int(config["feature"]["primary_safety_lag_ms"])
    primary_features = build_causal_features(paired, config, primary_lag)
    threshold_audit, selected_threshold = _threshold_audit(
        primary_features, calibration_dates, validation_dates, config
    )
    cooldown = int(config["frequency"]["cooldown_minutes"])
    role_by_date = dict(
        zip(coverage["date_utc"], coverage["frequency_role"], strict=True)
    )
    event_frames: list[pd.DataFrame] = []
    daily_frames: list[pd.DataFrame] = []
    lag_roles = [(primary_lag, "PRIMARY")]
    lag_roles.extend(
        (int(value), "CLOCK_ROBUSTNESS")
        for value in config["feature"]["robustness_safety_lags_ms"]
    )
    validation_rates: dict[str, float] = {}
    for lag, analysis_role in lag_roles:
        features = (
            primary_features
            if lag == primary_lag
            else build_causal_features(paired, config, lag)
        )
        events = select_candidate_episodes(features, selected_threshold, cooldown)
        event_frames.append(
            _event_output(events, selected_threshold, role_by_date, analysis_role)
        )
        counts = (
            events.groupby(["date_utc", "candidate_direction"])
            .size()
            .unstack(fill_value=0)
        )
        daily = coverage.loc[coverage["is_full_weekday"]].copy()
        daily["safety_lag_ms"] = lag
        daily["analysis_role"] = analysis_role
        daily["long_candidates"] = daily["date_utc"].map(
            counts.get(1, pd.Series(dtype=int))
        ).fillna(0).astype(int)
        daily["short_candidates"] = daily["date_utc"].map(
            counts.get(-1, pd.Series(dtype=int))
        ).fillna(0).astype(int)
        daily["candidate_count"] = (
            daily["long_candidates"] + daily["short_candidates"]
        )
        daily_frames.append(daily)
        validation_rates[str(lag)] = _event_rate(events, validation_dates)
    opportunities = pd.concat(event_frames, ignore_index=True)
    daily_frequency = pd.concat(daily_frames, ignore_index=True)
    primary_validation_daily = daily_frequency.loc[
        daily_frequency["safety_lag_ms"].eq(primary_lag)
        & daily_frequency["frequency_role"].eq("VALIDATION")
    ]
    primary_validation_events = opportunities.loc[
        opportunities["safety_lag_ms"].eq(primary_lag)
        & opportunities["frequency_role"].eq("VALIDATION")
    ]
    validation_rate = validation_rates[str(primary_lag)]
    active_share = float(
        primary_validation_daily["candidate_count"].gt(0).mean()
    )
    directions = primary_validation_events["candidate_side"].value_counts()
    minority_share = (
        float(directions.min() / directions.sum()) if len(directions) == 2 else 0.0
    )
    frequency = config["frequency"]
    primary_pass = (
        float(frequency["validation_min_candidates_per_day"])
        <= validation_rate
        <= float(frequency["validation_max_candidates_per_day"])
    )
    active_share_pass = active_share >= float(
        frequency["validation_min_active_day_share"]
    )
    direction_pass = minority_share >= float(
        frequency["validation_min_minority_direction_share"]
    )
    robustness_pass = all(
        float(frequency["robustness_min_candidates_per_day"])
        <= validation_rates[str(int(lag))]
        <= float(frequency["robustness_max_candidates_per_day"])
        for lag in config["feature"]["robustness_safety_lags_ms"]
    )
    passed = primary_pass and active_share_pass and direction_pass and robustness_pass
    audit: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "paired_quotes": int(len(paired)),
        "calibration_full_weekdays": calibration_dates,
        "validation_full_weekdays": validation_dates,
        "selected_z_threshold": selected_threshold,
        "primary_safety_lag_ms": primary_lag,
        "primary_calibration_candidates_per_day": float(
            threshold_audit.loc[
                threshold_audit["selected_by_frequency_calibration"],
                "calibration_candidates_per_day",
            ].iloc[0]
        ),
        "primary_validation_candidates_per_day": validation_rate,
        "primary_validation_active_day_share": active_share,
        "primary_validation_minority_direction_share": minority_share,
        "validation_candidates_per_day_by_safety_lag_ms": validation_rates,
        "primary_frequency_gate_pass": primary_pass,
        "active_day_share_gate_pass": active_share_pass,
        "direction_balance_gate_pass": direction_pass,
        "clock_robustness_gate_pass": robustness_pass,
        "opportunity_structure_gate_pass": passed,
        "decision": (
            "V22_2_OPPORTUNITY_STRUCTURE_PASS"
            if passed
            else "V22_2_OPPORTUNITY_STRUCTURE_FAIL"
        ),
        "future_prices_opened": False,
        "entry_fills_created": False,
        "exits_created": False,
        "labels_created": False,
        "pnl_calculated": False,
        "strategy_admission_authorized": False,
        "execution_authorized": False,
    }
    return opportunities, threshold_audit, daily_frequency, audit


def render_markdown(audit: dict[str, Any]) -> str:
    rates = audit["validation_candidates_per_day_by_safety_lag_ms"]
    return (
        "# Capital-Dukascopy Lagged Opportunity Audit V22.2\n\n"
        f"Decision: **{audit['decision']}**.\n\n"
        f"Selected z-threshold: **{audit['selected_z_threshold']:.2f}** from "
        "frequency calibration only. Primary validation frequency: "
        f"**{audit['primary_validation_candidates_per_day']:.3f}/day**.\n\n"
        f"Validation active-day share: "
        f"**{audit['primary_validation_active_day_share']:.2%}**; minority "
        f"direction share: **{audit['primary_validation_minority_direction_share']:.2%}**.\n\n"
        f"Clock robustness frequencies: 20 seconds **{rates['20000']:.3f}/day**, "
        f"30 seconds **{rates['30000']:.3f}/day**.\n\n"
        "No future price, entry fill, exit, label, P&L, or execution action was "
        "opened. A pass permits only a separately preregistered economic test.\n"
    )
