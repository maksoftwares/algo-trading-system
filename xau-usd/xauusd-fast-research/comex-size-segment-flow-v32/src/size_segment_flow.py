from __future__ import annotations

import hashlib
import itertools
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FILE_DATE = re.compile(r"(\d{8})\.trades\.dbn(?:\.zst)?$")
REQUIRED_COLUMNS = {"ts_event", "instrument_id", "side", "price", "size"}


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_date(path: Path) -> pd.Timestamp:
    match = FILE_DATE.search(path.name)
    if match is None:
        raise ValueError(f"Cannot parse source date from {path.name}")
    return pd.Timestamp(match.group(1), tz="UTC")


def discover_source_files(
    directory: Path, *, start: pd.Timestamp, end: pd.Timestamp
) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"COMEX source directory is missing: {directory}")
    files: list[Path] = []
    for path in directory.glob("*.trades.dbn*"):
        try:
            date = source_date(path)
        except ValueError:
            continue
        if start <= date < end:
            files.append(path)
    files.sort(key=source_date)
    if not files:
        raise FileNotFoundError(f"No COMEX trade files found for {start} to {end}")
    return files


def load_dbn_trades(path: Path) -> pd.DataFrame:
    import databento as db

    frame = db.DBNStore.from_file(path).to_df(
        price_type="float",
        pretty_ts=True,
        map_symbols=False,
        schema="trades",
    )
    if not isinstance(frame, pd.DataFrame):
        frame = pd.concat(frame, ignore_index=False)
    return frame


def normalize_trades(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "ts_event" not in result.columns and result.index.name == "ts_event":
        result = result.reset_index()
    missing = sorted(REQUIRED_COLUMNS - set(result.columns))
    if missing:
        raise ValueError(f"Trade data is missing required columns: {missing}")
    result["ts_event"] = pd.to_datetime(result["ts_event"], utc=True)
    result["instrument_id"] = pd.to_numeric(
        result["instrument_id"], errors="raise"
    ).astype("int64")
    result["price"] = pd.to_numeric(result["price"], errors="raise").astype(float)
    result["size"] = pd.to_numeric(result["size"], errors="raise").astype(float)
    if (result["size"] <= 0).any():
        raise ValueError("Trade size must be positive.")
    result["side"] = result["side"].astype(str).str.upper().str[0]
    if not result["side"].isin(["A", "B", "N"]).all():
        raise ValueError("Trade data contains an unsupported aggressor side.")
    result["aggressor_sign"] = result["side"].map({"B": 1.0, "A": -1.0, "N": 0.0})
    return result.sort_values(["ts_event", "instrument_id"], kind="stable").reset_index(
        drop=True
    )


def _minute_of_day(values: pd.Series, timezone: str) -> pd.Series:
    local = values.dt.tz_convert(timezone)
    return local.dt.hour * 60 + local.dt.minute + local.dt.second / 60.0


def _clock_minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":"))
    return hour * 60 + minute


def session_trades(frame: pd.DataFrame, rule: Mapping[str, Any]) -> pd.DataFrame:
    normalized = normalize_trades(frame)
    minutes = _minute_of_day(normalized["ts_event"], str(rule["timezone"]))
    start = _clock_minutes(str(rule["session_start"]))
    end = _clock_minutes(str(rule["session_end"]))
    return normalized.loc[(minutes >= start) & (minutes < end)].copy()


def session_quality(session: pd.DataFrame, rule: Mapping[str, Any]) -> dict[str, Any]:
    if session.empty:
        return {
            "eligible_full_weekday": False,
            "coverage_minutes": 0.0,
            "nonempty_bars": 0,
            "raw_trades": 0,
        }
    bar_minutes = int(rule["bar_minutes"])
    bar_start = session["ts_event"].dt.floor(f"{bar_minutes}min")
    coverage = (
        session["ts_event"].iloc[-1] - session["ts_event"].iloc[0]
    ).total_seconds() / 60
    nonempty = int(bar_start.nunique())
    date = session["ts_event"].iloc[0].date()
    return {
        "date_utc": str(date),
        "eligible_full_weekday": bool(
            pd.Timestamp(date).weekday() < 5
            and coverage >= float(rule["minimum_session_coverage_minutes"])
            and nonempty >= int(rule["minimum_nonempty_bars"])
        ),
        "coverage_minutes": float(coverage),
        "nonempty_bars": nonempty,
        "raw_trades": len(session),
        "instrument_ids": sorted(
            int(value) for value in session["instrument_id"].unique()
        ),
    }


def build_bar_features(
    session: pd.DataFrame,
    *,
    large_trade_size: int,
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if session.empty:
        return pd.DataFrame()
    frame = session.copy()
    bar_minutes = int(rule["bar_minutes"])
    frame["bar_start_utc"] = frame["ts_event"].dt.floor(f"{bar_minutes}min")
    frame["feature_time_utc"] = frame["bar_start_utc"] + pd.Timedelta(
        minutes=bar_minutes
    )
    small = frame["size"] <= int(rule["small_trade_maximum_size"])
    large = frame["size"] >= int(large_trade_size)
    known = frame["aggressor_sign"] != 0
    frame["small_volume"] = np.where(small & known, frame["size"], 0.0)
    frame["small_signed_volume"] = np.where(
        small & known, frame["size"] * frame["aggressor_sign"], 0.0
    )
    frame["large_volume"] = np.where(large & known, frame["size"], 0.0)
    frame["large_signed_volume"] = np.where(
        large & known, frame["size"] * frame["aggressor_sign"], 0.0
    )
    grouped = frame.groupby(
        ["instrument_id", "bar_start_utc", "feature_time_utc"],
        sort=True,
        observed=True,
    )
    bars = grouped.agg(
        first_event_utc=("ts_event", "first"),
        last_event_utc=("ts_event", "last"),
        trade_count=("size", "size"),
        total_volume=("size", "sum"),
        small_volume=("small_volume", "sum"),
        small_signed_volume=("small_signed_volume", "sum"),
        large_volume=("large_volume", "sum"),
        large_signed_volume=("large_signed_volume", "sum"),
        trade_price_open=("price", "first"),
        trade_price_last=("price", "last"),
    ).reset_index()
    bars["small_imbalance"] = np.divide(
        bars["small_signed_volume"],
        bars["small_volume"],
        out=np.zeros(len(bars), dtype=float),
        where=bars["small_volume"].to_numpy() > 0,
    )
    bars["large_imbalance"] = np.divide(
        bars["large_signed_volume"],
        bars["large_volume"],
        out=np.zeros(len(bars), dtype=float),
        where=bars["large_volume"].to_numpy() > 0,
    )
    if not (bars["last_event_utc"] < bars["feature_time_utc"]).all():
        raise ValueError(
            "A feature bar contains an event at or after its decision time."
        )
    bars["large_trade_size"] = int(large_trade_size)
    return bars


def generate_candidates(
    bars: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if bars.empty:
        return pd.DataFrame()
    large_sign = np.sign(bars["large_signed_volume"])
    mask = bars["large_volume"] >= float(policy["minimum_large_volume"])
    mask &= bars["large_imbalance"].abs() >= float(
        policy["minimum_absolute_large_imbalance"]
    )
    mask &= bars["small_volume"] >= float(rule["minimum_small_volume"])
    mask &= bars["small_imbalance"] * large_sign <= -float(
        policy["minimum_absolute_opposing_small_imbalance"]
    )
    mask &= large_sign != 0
    selected = bars.loc[mask].copy()
    if selected.empty:
        return selected
    selected["family"] = str(rule["family"])
    selected["direction"] = np.where(
        selected["large_signed_volume"] > 0, "LONG", "SHORT"
    )
    selected = selected.sort_values(
        ["feature_time_utc", "instrument_id"], kind="stable"
    ).reset_index(drop=True)
    cooldown = pd.Timedelta(minutes=int(rule["cooldown_minutes"]))
    retained: list[int] = []
    last_time: pd.Timestamp | None = None
    for index, row in selected.iterrows():
        decision = pd.Timestamp(row["feature_time_utc"])
        if last_time is None or decision - last_time >= cooldown:
            retained.append(index)
            last_time = decision
    result = selected.loc[retained].copy().reset_index(drop=True)
    decision_ms = result["feature_time_utc"].astype("int64") // 1_000_000
    result.insert(
        0,
        "candidate_id",
        result["family"].astype(str)
        + ":"
        + decision_ms.astype(str)
        + ":"
        + result["direction"].astype(str)
        + ":"
        + result["instrument_id"].astype(str),
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("Candidate generation produced duplicate IDs.")
    return result


def policy_grid(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    calibration = config["calibration"]
    rows = []
    for size, volume, large_imbalance, small_imbalance in itertools.product(
        calibration["large_trade_size_grid"],
        calibration["minimum_large_volume_grid"],
        calibration["minimum_absolute_large_imbalance_grid"],
        calibration["minimum_absolute_opposing_small_imbalance_grid"],
    ):
        rows.append(
            {
                "large_trade_size": int(size),
                "minimum_large_volume": int(volume),
                "minimum_absolute_large_imbalance": float(large_imbalance),
                "minimum_absolute_opposing_small_imbalance": float(small_imbalance),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"SZ{int(policy['large_trade_size']):02d}"
        f"__LV{int(policy['minimum_large_volume']):03d}"
        f"__LI{int(round(float(policy['minimum_absolute_large_imbalance']) * 100)):02d}"
        f"__SI{int(round(float(policy['minimum_absolute_opposing_small_imbalance']) * 100)):02d}"
    )


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    dates = list(eligible_dates)
    trades = len(candidates)
    if trades:
        candidate_dates = pd.to_datetime(
            candidates["feature_time_utc"], utc=True
        ).dt.date.astype(str)
        active_days = int(candidate_dates.nunique())
        long_trades = int((candidates["direction"] == "LONG").sum())
        short_trades = int((candidates["direction"] == "SHORT").sum())
    else:
        active_days = long_trades = short_trades = 0
    full_days = len(dates)
    frequency = trades / full_days if full_days else 0.0
    minority_share = min(long_trades, short_trades) / trades if trades else 0.0
    active_share = active_days / full_days if full_days else 0.0
    qualifies = bool(
        float(selection["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(selection["maximum_candidates_per_full_weekday"])
        and active_share >= float(selection["minimum_active_day_share"])
        and minority_share >= float(selection["minimum_minority_direction_share"])
    )
    return {
        "policy_id": policy_id(policy),
        **dict(policy),
        "eligible_full_weekdays": full_days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": long_trades,
        "short_candidates": short_trades,
        "minority_direction_share": minority_share,
        "selection_eligible": qualifies,
    }


def select_policy(
    rows: Iterable[Mapping[str, Any]], selection: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(selection["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -int(row["large_trade_size"]),
            -int(row["minimum_large_volume"]),
            -float(row["minimum_absolute_large_imbalance"]),
            -float(row["minimum_absolute_opposing_small_imbalance"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "large_trade_size",
        "minimum_large_volume",
        "minimum_absolute_large_imbalance",
        "minimum_absolute_opposing_small_imbalance",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None
    return positive / negative


def closed_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    peak = equity.cummax().clip(lower=0.0)
    return float((peak - equity).max())


def circular_block_bootstrap_pvalue(
    daily_values: np.ndarray,
    *,
    block_length: int,
    resamples: int,
    seed: int,
) -> float:
    values = np.asarray(daily_values, dtype=float)
    if values.size == 0 or float(values.mean()) <= 0:
        return 1.0
    centered = values - values.mean()
    rng = np.random.default_rng(seed)
    block_count = int(np.ceil(values.size / block_length))
    exceed = 0
    for _ in range(resamples):
        starts = rng.integers(0, values.size, size=block_count)
        sample = np.concatenate(
            [
                centered[(start + np.arange(block_length)) % values.size]
                for start in starts
            ]
        )[: values.size]
        exceed += int(float(sample.mean()) >= float(values.mean()))
    return (exceed + 1) / (resamples + 1)


def summarize_stage(
    labels: pd.DataFrame,
    *,
    stage: str,
    eligible_dates: Sequence[str],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    resolved = labels.loc[labels["status"] == "RESOLVED"].copy()
    if resolved.empty:
        resolved = pd.DataFrame(
            columns=[
                "candidate_id",
                "direction",
                "decision_time_utc",
                "exit_time_utc",
                "baseline_net_pnl_usd",
                "stress_net_pnl_usd",
            ]
        )
    else:
        resolved["exit_time_utc"] = pd.to_datetime(resolved["exit_time_utc"], utc=True)
        resolved = resolved.sort_values(
            ["exit_time_utc", "candidate_id"], kind="stable"
        )
    base = resolved["baseline_net_pnl_usd"].astype(float)
    stress = resolved["stress_net_pnl_usd"].astype(float)
    resolved["date_utc"] = pd.to_datetime(
        resolved["decision_time_utc"], utc=True
    ).dt.date.astype(str)
    full_dates = list(eligible_dates)
    daily = (
        resolved.groupby("date_utc", sort=True)["stress_net_pnl_usd"]
        .sum()
        .reindex(full_dates, fill_value=0.0)
    )
    monthly = daily.groupby(pd.PeriodIndex(pd.to_datetime(daily.index), freq="M")).sum()
    midpoint = len(resolved) // 2
    first = stress.iloc[:midpoint]
    second = stress.iloc[midpoint:]
    removed = stress.drop(
        stress.nlargest(int(config["gates"]["top_winners_removed"])).index
    )
    bootstrap = config["gates"]["bootstrap"]
    pvalue = circular_block_bootstrap_pvalue(
        daily.to_numpy(dtype=float),
        block_length=int(bootstrap["block_weekdays"]),
        resamples=int(bootstrap["resamples"]),
        seed=int(bootstrap["seed"]),
    )
    trades = len(resolved)
    days = len(full_dates)
    metrics = {
        "stage": stage,
        "eligible_full_weekdays": days,
        "resolved_trades": trades,
        "trades_per_full_weekday": trades / days if days else 0.0,
        "long_trades": int((resolved["direction"] == "LONG").sum()),
        "short_trades": int((resolved["direction"] == "SHORT").sum()),
        "base_net_pnl_usd": float(base.sum()),
        "stress_net_pnl_usd": float(stress.sum()),
        "base_profit_factor": profit_factor(base),
        "stress_profit_factor": profit_factor(stress),
        "mean_stress_pnl_usd": float(stress.mean()) if trades else 0.0,
        "profitable_day_share": float((daily > 0).mean()) if days else 0.0,
        "positive_month_share": float((monthly > 0).mean()) if len(monthly) else 0.0,
        "first_half_stress_profit_factor": profit_factor(first),
        "second_half_stress_profit_factor": profit_factor(second),
        "top_winners_removed_stress_net_usd": float(removed.sum()),
        "closed_trade_stress_drawdown_usd": closed_drawdown(stress),
        "daily_block_bootstrap_one_sided_pvalue": pvalue,
    }
    minimum_direction = float(config["gates"]["minimum_direction_share"])
    base_pf = metrics["base_profit_factor"] or 0.0
    stress_pf = metrics["stress_profit_factor"] or 0.0
    first_pf = metrics["first_half_stress_profit_factor"] or 0.0
    second_pf = metrics["second_half_stress_profit_factor"] or 0.0
    long_share = metrics["long_trades"] / trades if trades else 0.0
    short_share = metrics["short_trades"] / trades if trades else 0.0
    checks = {
        "minimum_resolved_trades": trades
        >= int(config["gates"]["minimum_resolved_trades"][stage]),
        "minimum_frequency": metrics["trades_per_full_weekday"]
        >= float(config["gates"]["minimum_trades_per_full_weekday"]),
        "maximum_frequency": metrics["trades_per_full_weekday"]
        <= float(config["gates"]["maximum_trades_per_full_weekday"]),
        "positive_base_net": metrics["base_net_pnl_usd"] > 0,
        "positive_stress_net": metrics["stress_net_pnl_usd"] > 0,
        "positive_mean_stress": metrics["mean_stress_pnl_usd"] > 0,
        "minimum_base_profit_factor": base_pf
        >= float(config["gates"]["minimum_base_profit_factor"]),
        "minimum_stress_profit_factor": stress_pf
        >= float(config["gates"]["minimum_stress_profit_factor"]),
        "minimum_profitable_day_share": metrics["profitable_day_share"]
        >= float(config["gates"]["minimum_profitable_day_share"]),
        "minimum_positive_month_share": metrics["positive_month_share"]
        >= float(config["gates"]["minimum_positive_month_share"]),
        "direction_balance": long_share >= minimum_direction
        and short_share >= minimum_direction,
        "first_half_profit_factor": first_pf
        >= float(config["gates"]["minimum_half_stress_profit_factor"]),
        "second_half_profit_factor": second_pf
        >= float(config["gates"]["minimum_half_stress_profit_factor"]),
        "top_winners_removed_positive": metrics["top_winners_removed_stress_net_usd"]
        > 0,
        "maximum_drawdown": metrics["closed_trade_stress_drawdown_usd"]
        <= float(config["gates"]["maximum_closed_trade_drawdown_usd"]),
        "bootstrap_significance": pvalue
        <= float(config["gates"]["bootstrap"]["maximum_one_sided_pvalue"]),
    }
    return {
        "metrics": metrics,
        "gate_checks": checks,
        "gate_passed": all(checks.values()),
    }
