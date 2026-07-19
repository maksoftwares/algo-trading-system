from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = (
    "schema_version",
    "timestamp_utc",
    "tick_time_msc",
    "account_login",
    "account_server",
    "symbol",
    "bid",
    "ask",
    "spread_price",
)
DATE_PATTERN = re.compile(r"_ticks_(\d{8})\.csv$")
FEATURE_COLUMNS = (
    "timestamp_utc",
    "tick_time_msc",
    "date_utc",
    "utc_block_start_ms",
    "bid",
    "ask",
    "mid",
    "spread_price",
    "lookback_source_time_msc",
    "boundary_quote_age_ms",
    "maximum_internal_quote_gap_ms",
    "nonzero_mid_updates",
    "signed_update_imbalance",
    "displacement_price",
    "candidate_gate",
    "raw_gate_crossing",
)
CANDIDATE_COLUMNS = (*FEATURE_COLUMNS, "candidate_side")


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_quote_microburst_forward_v24_1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: dict[str, Any], omitted_key: str) -> str:
    normalized = dict(payload)
    normalized.pop(omitted_key, None)
    encoded = json.dumps(
        normalized,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()).replace("\\", "/"),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def source_date(path: Path) -> pd.Timestamp:
    match = DATE_PATTERN.search(path.name)
    if match is None:
        raise ValueError(f"V24 tick filename has no YYYYMMDD date: {path}")
    return pd.Timestamp(match.group(1), tz="UTC")


def discover_source_files(config: dict[str, Any]) -> list[Path]:
    source = config["source"]
    directory = Path(source["directory"])
    return sorted(directory.glob(str(source["filename_glob"])))


def verify_manifest_files(manifest: dict[str, Any], key: str) -> None:
    for record in manifest[key]:
        path = Path(record["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if int(path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"V24 source size changed: {path}")
        if sha256_file(path) != str(record["sha256"]):
            raise ValueError(f"V24 source hash changed: {path}")


def _parse_timestamp_ms(values: pd.Series) -> np.ndarray:
    parsed = pd.to_datetime(
        values,
        format="%Y.%m.%d %H:%M:%S.%fZ",
        utc=True,
        errors="coerce",
    )
    if parsed.isna().any():
        raise ValueError("V24 source contains an invalid timestamp_utc")
    return parsed.array.as_unit("ms").asi8.astype(np.int64, copy=False)


def load_ticks(
    paths: Iterable[Path], config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    source = config["source"]
    quality = config["data_quality"]
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    source_file_order = 0
    for path in sorted(Path(value) for value in paths):
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, usecols=list(REQUIRED_COLUMNS))
        record = file_record(path)
        record["source_date_utc"] = source_date(path).strftime("%Y-%m-%d")
        record["raw_rows"] = int(len(frame))
        records.append(record)
        if frame.empty:
            source_file_order += 1
            continue
        if not frame["schema_version"].eq(source["schema_version"]).all():
            raise ValueError(f"V24 schema mismatch: {path}")
        if not frame["account_login"].eq(int(source["account_login"])).all():
            raise ValueError(f"V24 account mismatch: {path}")
        if not frame["account_server"].eq(source["account_server"]).all():
            raise ValueError(f"V24 server mismatch: {path}")
        if not frame["symbol"].eq(source["symbol"]).all():
            raise ValueError(f"V24 symbol mismatch: {path}")
        for column in ("tick_time_msc", "bid", "ask", "spread_price"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[["tick_time_msc", "bid", "ask", "spread_price"]].isna().any().any():
            raise ValueError(f"V24 source contains invalid numeric values: {path}")
        frame["tick_time_msc"] = frame["tick_time_msc"].astype(np.int64)
        parsed_ms = _parse_timestamp_ms(frame["timestamp_utc"])
        disagreement = np.abs(
            parsed_ms - frame["tick_time_msc"].to_numpy(dtype=np.int64)
        )
        if bool(
            np.any(disagreement > int(quality["maximum_timestamp_disagreement_ms"]))
        ):
            raise ValueError(f"V24 timestamp disagreement: {path}")
        bid = frame["bid"].to_numpy(dtype=float)
        ask = frame["ask"].to_numpy(dtype=float)
        spread = frame["spread_price"].to_numpy(dtype=float)
        if bool(np.any((bid <= 0.0) | (ask < bid) | (spread < 0.0))):
            raise ValueError(f"V24 source contains invalid quotes: {path}")
        spread_error = np.abs((ask - bid) - spread)
        if bool(np.any(spread_error > float(quality["maximum_spread_field_error"]))):
            raise ValueError(f"V24 spread field mismatch: {path}")
        frame["source_file_order"] = source_file_order
        frame["source_row"] = np.arange(len(frame), dtype=np.int64)
        frame["source_path"] = str(path.resolve()).replace("\\", "/")
        frames.append(frame)
        source_file_order += 1
    if not frames:
        empty = pd.DataFrame(columns=[*REQUIRED_COLUMNS, "date_utc"])
        return (
            empty,
            {"source_files": records, "raw_rows": 0, "unique_rows": 0},
            pd.DataFrame(),
        )

    raw = pd.concat(frames, ignore_index=True)
    raw["date_utc"] = pd.to_datetime(
        raw["tick_time_msc"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%d")
    raw_daily = (
        raw.groupby("date_utc", as_index=False)
        .agg(
            raw_rows=("tick_time_msc", "size"),
            unique_milliseconds=("tick_time_msc", "nunique"),
        )
        .sort_values("date_utc")
    )
    raw_daily["duplicate_millisecond_rows"] = (
        raw_daily["raw_rows"] - raw_daily["unique_milliseconds"]
    )
    raw_daily["duplicate_millisecond_share"] = (
        raw_daily["duplicate_millisecond_rows"] / raw_daily["raw_rows"]
    )
    ordered = raw.sort_values(
        ["tick_time_msc", "source_file_order", "source_row"],
        kind="mergesort",
    )
    ticks = (
        ordered.drop_duplicates("tick_time_msc", keep="last")
        .sort_values("tick_time_msc", kind="mergesort")
        .reset_index(drop=True)
    )
    timestamps = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    if bool(np.any(np.diff(timestamps) <= 0)):
        raise ValueError("V24 deduplicated timestamps are not strictly increasing")
    ticks["timestamp_utc"] = pd.to_datetime(
        ticks["tick_time_msc"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    audit = {
        "source_files": records,
        "raw_rows": int(len(raw)),
        "unique_rows": int(len(ticks)),
        "duplicate_millisecond_rows": int(len(raw) - len(ticks)),
        "daily_source_quality": raw_daily.to_dict(orient="records"),
    }
    return ticks, audit, raw_daily


def _rolling_internal_max_gap(gaps: np.ndarray, starts: np.ndarray) -> np.ndarray:
    maximum = np.zeros(len(gaps), dtype=np.int64)
    candidates: deque[int] = deque()
    for index in range(len(gaps)):
        while candidates and candidates[0] <= int(starts[index]):
            candidates.popleft()
        if index > int(starts[index]):
            while candidates and gaps[candidates[-1]] <= gaps[index]:
                candidates.pop()
            candidates.append(index)
        maximum[index] = gaps[candidates[0]] if candidates else 0
    return maximum


def generate_candidates(
    ticks: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if ticks.empty:
        return (
            pd.DataFrame(columns=CANDIDATE_COLUMNS),
            pd.DataFrame(columns=FEATURE_COLUMNS),
        )
    feature = config["feature"]
    episode = config["episode"]
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    bid = ticks["bid"].to_numpy(dtype=float)
    ask = ticks["ask"].to_numpy(dtype=float)
    spread = ticks["spread_price"].to_numpy(dtype=float)
    mid = (bid + ask) / 2.0
    target = times - int(feature["lookback_ms"])
    starts = np.searchsorted(times, target, side="right") - 1
    valid_start = starts >= 0
    safe_starts = np.maximum(starts, 0)
    boundary_age = target - times[safe_starts]
    mid_delta = np.diff(mid, prepend=mid[0])
    update_sign = np.sign(mid_delta)
    nonzero = update_sign != 0
    signed_prefix = np.concatenate(([0.0], np.cumsum(update_sign)))
    count_prefix = np.concatenate(([0], np.cumsum(nonzero.astype(np.int64))))
    indices = np.arange(len(times), dtype=np.int64)
    update_sum = signed_prefix[indices + 1] - signed_prefix[safe_starts + 1]
    update_count = count_prefix[indices + 1] - count_prefix[safe_starts + 1]
    imbalance = np.divide(
        update_sum,
        update_count,
        out=np.zeros(len(times), dtype=float),
        where=update_count > 0,
    )
    displacement = mid - mid[safe_starts]
    gaps = np.diff(times, prepend=times[0])
    maximum_internal_gap = _rolling_internal_max_gap(gaps, safe_starts)
    direction_agrees = (np.sign(imbalance) == np.sign(displacement)) & (
        np.sign(displacement) != 0
    )
    gate = (
        valid_start
        & (boundary_age >= 0)
        & (boundary_age <= int(feature["maximum_boundary_quote_age_ms"]))
        & (maximum_internal_gap <= int(feature["maximum_internal_quote_gap_ms"]))
        & (spread <= float(feature["maximum_spread_price"]))
        & (update_count >= int(feature["minimum_nonzero_mid_updates"]))
        & (np.abs(imbalance) >= float(feature["minimum_absolute_update_imbalance"]))
        & (
            np.abs(displacement)
            >= float(feature["minimum_absolute_displacement_price"])
        )
        & direction_agrees
    )
    prior_gate = np.r_[False, gate[:-1]]
    prior_is_contiguous = np.r_[
        False,
        np.diff(times) <= int(feature["maximum_internal_quote_gap_ms"]),
    ]
    rising = gate & ~(prior_gate & prior_is_contiguous)
    block_ms = int(episode["utc_block_hours"]) * 60 * 60 * 1000
    block_start_ms = (times // block_ms) * block_ms
    timestamp = pd.to_datetime(times, unit="ms", utc=True)
    features = pd.DataFrame(
        {
            "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "tick_time_msc": times,
            "date_utc": timestamp.strftime("%Y-%m-%d"),
            "utc_block_start_ms": block_start_ms,
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread_price": spread,
            "lookback_source_time_msc": times[safe_starts],
            "boundary_quote_age_ms": boundary_age,
            "maximum_internal_quote_gap_ms": maximum_internal_gap,
            "nonzero_mid_updates": update_count,
            "signed_update_imbalance": imbalance,
            "displacement_price": displacement,
            "candidate_gate": gate,
            "raw_gate_crossing": rising,
        }
    )
    candidates = features.loc[features["raw_gate_crossing"]].copy()
    candidates = candidates.drop_duplicates(
        "utc_block_start_ms", keep="first"
    ).reset_index(drop=True)
    candidates["candidate_side"] = np.where(
        candidates["signed_update_imbalance"].gt(0), "LONG", "SHORT"
    )
    candidates = candidates.loc[:, CANDIDATE_COLUMNS]
    daily_maximum = int(episode["maximum_candidates_per_utc_day"])
    if (
        not candidates.empty
        and int(candidates.groupby("date_utc").size().max()) > daily_maximum
    ):
        raise ValueError("V24 candidate count exceeded its structural daily cap")
    return candidates, features


def assess_full_days(
    ticks: pd.DataFrame,
    raw_daily: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    quality = config["data_quality"]
    records: list[dict[str, Any]] = []
    for date_utc, group in ticks.groupby("date_utc", sort=True):
        times = group["tick_time_msc"].to_numpy(dtype=np.int64)
        day_start = pd.Timestamp(date_utc, tz="UTC")
        start_offset_hours = float(
            (times[0] - day_start.value // 1_000_000) / 3_600_000
        )
        end_offset_hours = float((times[-1] - day_start.value // 1_000_000) / 3_600_000)
        gaps = np.diff(times)
        p99_gap = float(np.quantile(gaps, 0.99)) if len(gaps) else 999999.0
        records.append(
            {
                "date_utc": date_utc,
                "weekday": int(day_start.weekday()),
                "unique_quotes": int(len(group)),
                "start_offset_hours": start_offset_hours,
                "end_offset_hours": end_offset_hours,
                "p99_interquote_gap_ms": p99_gap,
            }
        )
    daily = pd.DataFrame(records)
    if daily.empty:
        return daily
    daily = daily.merge(raw_daily, on="date_utc", how="left", validate="one_to_one")
    daily["eligible_full_weekday"] = (
        daily["weekday"].lt(5)
        & daily["unique_quotes"].ge(int(quality["minimum_unique_quotes_per_full_day"]))
        & daily["start_offset_hours"].le(float(quality["latest_day_start_hour_utc"]))
        & daily["end_offset_hours"].ge(float(quality["earliest_day_end_hour_utc"]))
        & daily["p99_interquote_gap_ms"].le(
            float(quality["maximum_p99_interquote_gap_ms"])
        )
        & daily["duplicate_millisecond_share"].le(
            float(quality["maximum_duplicate_millisecond_share"])
        )
    )
    return daily.sort_values("date_utc").reset_index(drop=True)


def simulate_trades(
    ticks: pd.DataFrame,
    candidates: pd.DataFrame,
    eligible_dates: list[str],
    partition: str,
    config: dict[str, Any],
) -> pd.DataFrame:
    simulation = config["simulation"]
    selected = candidates.loc[candidates["date_utc"].isin(eligible_dates)]
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    records: list[dict[str, Any]] = []
    hold_ms = int(simulation["hold_seconds"]) * 1000
    for _, candidate in selected.iterrows():
        candidate_ms = int(candidate["tick_time_msc"])
        entry_index = int(np.searchsorted(times, candidate_ms, side="right"))
        if entry_index >= len(ticks):
            continue
        entry = ticks.iloc[entry_index]
        entry_ms = int(entry["tick_time_msc"])
        if entry_ms - candidate_ms > int(simulation["maximum_entry_delay_ms"]):
            continue
        target_exit_ms = entry_ms + hold_ms
        exit_index = int(np.searchsorted(times, target_exit_ms, side="left"))
        if exit_index >= len(ticks):
            continue
        exit_quote = ticks.iloc[exit_index]
        exit_ms = int(exit_quote["tick_time_msc"])
        if exit_ms - target_exit_ms > int(simulation["maximum_exit_delay_ms"]):
            continue
        side = str(candidate["candidate_side"])
        if side == "LONG":
            observed_entry = float(entry["ask"])
            observed_exit = float(exit_quote["bid"])
            observed_move = observed_exit - observed_entry
        elif side == "SHORT":
            observed_entry = float(entry["bid"])
            observed_exit = float(exit_quote["ask"])
            observed_move = observed_entry - observed_exit
        else:
            raise ValueError(f"Unknown V24 side: {side}")
        dollars_per_unit = float(simulation["dollars_per_price_unit"])
        base_pnl = (
            observed_move - 2.0 * float(simulation["base_slippage_per_side_price"])
        ) * dollars_per_unit
        stress_pnl = (
            observed_move - 2.0 * float(simulation["stress_slippage_per_side_price"])
        ) * dollars_per_unit
        records.append(
            {
                "evidence_partition": partition,
                "date_utc": candidate["date_utc"],
                "utc_block_start_ms": int(candidate["utc_block_start_ms"]),
                "candidate_time_utc": candidate["timestamp_utc"],
                "candidate_time_msc": candidate_ms,
                "side": side,
                "signed_update_imbalance": float(candidate["signed_update_imbalance"]),
                "displacement_price": float(candidate["displacement_price"]),
                "entry_time_msc": entry_ms,
                "entry_delay_ms": entry_ms - candidate_ms,
                "entry_bid": float(entry["bid"]),
                "entry_ask": float(entry["ask"]),
                "exit_time_msc": exit_ms,
                "exit_delay_ms": exit_ms - target_exit_ms,
                "exit_bid": float(exit_quote["bid"]),
                "exit_ask": float(exit_quote["ask"]),
                "observed_bidask_move": observed_move,
                "base_pnl_dollars": base_pnl,
                "stress_pnl_dollars": stress_pnl,
                "reference_lot": float(simulation["reference_lot"]),
            }
        )
    columns = (
        "evidence_partition",
        "date_utc",
        "utc_block_start_ms",
        "candidate_time_utc",
        "candidate_time_msc",
        "side",
        "signed_update_imbalance",
        "displacement_price",
        "entry_time_msc",
        "entry_delay_ms",
        "entry_bid",
        "entry_ask",
        "exit_time_msc",
        "exit_delay_ms",
        "exit_bid",
        "exit_ask",
        "observed_bidask_move",
        "base_pnl_dollars",
        "stress_pnl_dollars",
        "reference_lot",
    )
    return pd.DataFrame(records, columns=columns)


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values.loc[values.gt(0)].sum())
    gross_loss = float(-values.loc[values.lt(0)].sum())
    if gross_loss <= 0.0:
        return 999999.0 if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def closed_trade_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.cumsum().to_numpy(dtype=float)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def evaluate_stage(
    trades: pd.DataFrame,
    stage_dates: list[str],
    partition: str,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    gates = config["gates"]
    selected = trades.loc[
        trades["evidence_partition"].eq(partition)
        & trades["date_utc"].isin(stage_dates)
    ].sort_values("entry_time_msc", kind="mergesort")
    base = selected["base_pnl_dollars"].astype(float)
    stress = selected["stress_pnl_dollars"].astype(float)
    observed_daily = (
        selected.groupby("date_utc", as_index=False)
        .agg(
            trades=("date_utc", "size"),
            base_pnl_dollars=("base_pnl_dollars", "sum"),
            stress_pnl_dollars=("stress_pnl_dollars", "sum"),
        )
        .sort_values("date_utc")
    )
    daily = pd.DataFrame({"date_utc": stage_dates}).merge(
        observed_daily, on="date_utc", how="left", validate="one_to_one"
    )
    for column in ("trades", "base_pnl_dollars", "stress_pnl_dollars"):
        daily[column] = daily[column].fillna(0)
    daily["trades"] = daily["trades"].astype(int)
    base_net = float(base.sum())
    stress_net = float(stress.sum())
    drawdown = closed_trade_drawdown(base) if len(base) else 0.0
    recovery = (
        base_net / drawdown if drawdown > 0.0 else (999999.0 if base_net > 0.0 else 0.0)
    )
    midpoint = len(stage_dates) // 2
    first_half = selected.loc[selected["date_utc"].isin(stage_dates[:midpoint])]
    second_half = selected.loc[selected["date_utc"].isin(stage_dates[midpoint:])]
    long_share = float(selected["side"].eq("LONG").mean()) if len(selected) else 0.0
    short_share = float(selected["side"].eq("SHORT").mean()) if len(selected) else 0.0
    daily_values = daily["base_pnl_dollars"].to_numpy(dtype=float)
    rng = np.random.default_rng(int(gates["daily_bootstrap_seed"]))
    bootstrap = rng.choice(
        daily_values,
        size=(int(gates["daily_bootstrap_samples"]), len(daily_values)),
        replace=True,
    ).mean(axis=1)
    bootstrap_lower = float(
        np.quantile(bootstrap, float(gates["daily_bootstrap_lower_quantile"]))
    )
    metrics = {
        "evidence_partition": partition,
        "full_weekdays": int(len(stage_dates)),
        "trades": int(len(selected)),
        "trades_per_full_weekday": float(len(selected) / len(stage_dates)),
        "long_trades": int(selected["side"].eq("LONG").sum()),
        "short_trades": int(selected["side"].eq("SHORT").sum()),
        "long_share": long_share,
        "short_share": short_share,
        "base_net_pnl_dollars": base_net,
        "base_profit_factor": profit_factor(base),
        "base_win_rate": float(base.gt(0).mean()) if len(base) else 0.0,
        "base_mean_pnl_dollars": float(base.mean()) if len(base) else 0.0,
        "stress_net_pnl_dollars": stress_net,
        "stress_profit_factor": profit_factor(stress),
        "profitable_day_share": float(daily["base_pnl_dollars"].gt(0).mean()),
        "closed_trade_drawdown_dollars": drawdown,
        "recovery_factor": float(recovery),
        "first_half_profit_factor": profit_factor(
            first_half["base_pnl_dollars"].astype(float)
        ),
        "second_half_profit_factor": profit_factor(
            second_half["base_pnl_dollars"].astype(float)
        ),
        "daily_bootstrap_mean_lower_bound_dollars": bootstrap_lower,
    }
    checks = {
        "minimum_executable_trades": metrics["trades"]
        >= int(gates["minimum_executable_trades"]),
        "minimum_frequency": metrics["trades_per_full_weekday"]
        >= float(gates["minimum_trades_per_full_weekday"]),
        "maximum_frequency": metrics["trades_per_full_weekday"]
        <= float(gates["maximum_trades_per_full_weekday"]),
        "direction_balance": min(long_share, short_share)
        >= float(gates["minimum_direction_share"]),
        "positive_base_net": (not gates["require_positive_base_net"] or base_net > 0.0),
        "minimum_base_profit_factor": metrics["base_profit_factor"]
        >= float(gates["minimum_base_profit_factor"]),
        "positive_stress_net": (
            not gates["require_positive_stress_net"] or stress_net > 0.0
        ),
        "minimum_stress_profit_factor": metrics["stress_profit_factor"]
        >= float(gates["minimum_stress_profit_factor"]),
        "minimum_profitable_day_share": metrics["profitable_day_share"]
        >= float(gates["minimum_profitable_day_share"]),
        "maximum_closed_trade_drawdown": drawdown
        <= float(gates["maximum_closed_trade_drawdown_dollars"]),
        "minimum_recovery_factor": recovery >= float(gates["minimum_recovery_factor"]),
        "first_half_profit_factor": metrics["first_half_profit_factor"]
        >= float(gates["minimum_half_profit_factor"]),
        "second_half_profit_factor": metrics["second_half_profit_factor"]
        >= float(gates["minimum_half_profit_factor"]),
        "daily_bootstrap_lower_bound": (
            not gates["require_daily_bootstrap_lower_bound_positive"]
            or bootstrap_lower > 0.0
        ),
    }
    audit = {
        "schema_version": "xauusd_v24_1_forward_stage_audit",
        "evidence_partition": partition,
        "stage_dates": stage_dates,
        "metrics": metrics,
        "gate_checks": checks,
        "gate_passed": bool(all(checks.values())),
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    daily.insert(0, "evidence_partition", partition)
    return audit, daily
