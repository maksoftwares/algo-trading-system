from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FILENAME_DATE = re.compile(r"(\d{8})\.trades\.dbn(?:\.zst)?$")
ACCEPTANCE = "COMEX_PRIOR_VALUE_ACCEPTANCE_CONTINUATION_V1"
FAILED_AUCTION = "COMEX_PRIOR_VALUE_FAILED_AUCTION_V1"
OPENING_MIGRATION = "COMEX_OPENING_VALUE_MIGRATION_V1"
FAMILIES = (ACCEPTANCE, FAILED_AUCTION, OPENING_MIGRATION)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dbn_trades(path: Path) -> pd.DataFrame:
    import databento as db

    frame = db.DBNStore.from_file(path).to_df(
        price_type="float", pretty_ts=True, map_symbols=False, schema="trades"
    )
    if not isinstance(frame, pd.DataFrame):
        frame = pd.concat(frame, ignore_index=False)
    if frame.index.name == "ts_event" and "ts_event" not in frame.columns:
        frame = frame.reset_index()
    required = {"ts_event", "price", "size", "side"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"DBN trade file is missing {missing}: {path}")
    return frame[["ts_event", "price", "size", "side"]].copy()


def discover_sources(job_directory: Path, start: pd.Timestamp, end: pd.Timestamp) -> list[Path]:
    sources: list[Path] = []
    for path in job_directory.rglob("*.dbn.zst"):
        match = FILENAME_DATE.search(path.name)
        if not match:
            continue
        day = pd.Timestamp(match.group(1), tz="UTC")
        if start.floor("D") <= day < end.ceil("D"):
            sources.append(path)
    if not sources:
        raise FileNotFoundError(f"No DBN trade files found under {job_directory}")
    return sorted(sources)


def _seconds(text: str) -> int:
    hour, minute = (int(value) for value in text.split(":"))
    return hour * 3600 + minute * 60


def contiguous_value_area(
    prices: pd.Series,
    sizes: pd.Series,
    *,
    price_bin: float,
    fraction: float,
) -> tuple[float, float, float]:
    if not 0 < fraction <= 1 or price_bin <= 0:
        raise ValueError("Invalid value-area geometry")
    bins = np.rint(prices.to_numpy(dtype=float) / price_bin).astype(np.int64)
    volume = pd.Series(sizes.to_numpy(dtype=float)).groupby(bins, sort=True).sum()
    return _value_area_from_volume(volume, price_bin=price_bin, fraction=fraction)


def _value_area_from_volume(
    volume: pd.Series, *, price_bin: float, fraction: float
) -> tuple[float, float, float]:
    if volume.empty or float(volume.sum()) <= 0:
        raise ValueError("Cannot build a value area without positive volume")
    poc_candidates = volume.loc[volume.eq(volume.max())].index.to_numpy(dtype=np.int64)
    weighted_mean = float(np.average(volume.index.to_numpy(dtype=float), weights=volume.to_numpy()))
    poc = int(poc_candidates[np.argmin(np.abs(poc_candidates - weighted_mean))])
    selected = {poc}
    accumulated = float(volume.get(poc, 0.0))
    target = float(volume.sum()) * fraction
    low = high = poc
    while accumulated < target:
        below, above = low - 1, high + 1
        below_volume = float(volume.get(below, 0.0))
        above_volume = float(volume.get(above, 0.0))
        if below_volume == 0 and above_volume == 0:
            remaining = [int(value) for value in volume.index if int(value) not in selected]
            if not remaining:
                break
            nearest = min(remaining, key=lambda value: (min(abs(value - low), abs(value - high)), value))
            selected.add(nearest)
            low, high = min(low, nearest), max(high, nearest)
            accumulated += float(volume.loc[nearest])
        elif above_volume > below_volume:
            selected.add(above)
            high = above
            accumulated += above_volume
        else:
            selected.add(below)
            low = below
            accumulated += below_volume
    return (
        round(poc * price_bin, 10),
        round(low * price_bin, 10),
        round(high * price_bin, 10),
    )


def aggregate_session(trades: pd.DataFrame, auction: dict[str, Any]) -> pd.DataFrame:
    frame = trades.copy()
    frame["ts_event"] = pd.to_datetime(frame["ts_event"], utc=True)
    frame["price"] = pd.to_numeric(frame["price"], errors="raise")
    frame["size"] = pd.to_numeric(frame["size"], errors="raise")
    frame["side"] = frame["side"].astype(str).str.upper().str[0]
    local = frame["ts_event"].dt.tz_convert(auction["timezone"])
    seconds = local.dt.hour * 3600 + local.dt.minute * 60 + local.dt.second
    mask = (seconds >= _seconds(auction["session_start"])) & (
        seconds < _seconds(auction["session_end"])
    )
    frame = frame.loc[mask].copy()
    if frame.empty:
        return pd.DataFrame()
    local = frame["ts_event"].dt.tz_convert(auction["timezone"])
    frame["session_date"] = local.dt.strftime("%Y-%m-%d")
    frame["bucket"] = frame["ts_event"].dt.floor("5min")
    frame["signed_size"] = frame["size"] * frame["side"].map({"B": 1.0, "A": -1.0}).fillna(0.0)
    frame["pv"] = frame["price"] * frame["size"]
    rows: list[pd.DataFrame] = []
    for session_date, session in frame.groupby("session_date", sort=True, observed=True):
        poc, value_low, value_high = contiguous_value_area(
            session["price"],
            session["size"],
            price_bin=float(auction["price_bin"]),
            fraction=float(auction["value_area_fraction"]),
        )
        grouped = session.groupby("bucket", sort=True, observed=True)
        bars = grouped.agg(
            open=("price", "first"),
            high=("price", "max"),
            low=("price", "min"),
            close=("price", "last"),
            volume=("size", "sum"),
            signed_volume=("signed_size", "sum"),
            pv=("pv", "sum"),
            trade_count=("size", "size"),
        ).reset_index()
        running_poc: list[float] = []
        running_volume = pd.Series(dtype=float)
        price_bin = float(auction["price_bin"])
        for bucket, bucket_events in session.groupby("bucket", sort=True, observed=True):
            bins = np.rint(bucket_events["price"].to_numpy(dtype=float) / price_bin).astype(np.int64)
            additions = pd.Series(bucket_events["size"].to_numpy(dtype=float)).groupby(
                bins, sort=True
            ).sum()
            running_volume = running_volume.add(additions, fill_value=0.0).sort_index()
            current_poc, _, _ = _value_area_from_volume(
                running_volume,
                price_bin=price_bin,
                fraction=float(auction["value_area_fraction"]),
            )
            running_poc.append(current_poc)
        bars["session_date"] = session_date
        bars["session_bar_index"] = np.arange(len(bars), dtype=int)
        bars["running_poc"] = running_poc
        bars["session_poc"] = poc
        bars["session_value_low"] = value_low
        bars["session_value_high"] = value_high
        bars["cumulative_volume"] = bars["volume"].cumsum()
        bars["cumulative_signed_volume"] = bars["signed_volume"].cumsum()
        bars["cumulative_delta_ratio"] = (
            bars["cumulative_signed_volume"] / bars["cumulative_volume"].replace(0.0, np.nan)
        )
        bars["available_time_utc"] = bars["bucket"] + pd.Timedelta(minutes=5)
        local_available = bars["available_time_utc"].dt.tz_convert(auction["timezone"])
        bars["available_local_time"] = local_available.dt.strftime("%H:%M")
        rows.append(bars)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_cache(config: dict[str, Any], *, force: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["comex_source"]
    output = Path(source["cache"])
    daily_root = Path(source["daily_cache_directory"])
    output.parent.mkdir(parents=True, exist_ok=True)
    daily_root.mkdir(parents=True, exist_ok=True)
    start, end = pd.Timestamp(source["start_utc"]), pd.Timestamp(source["end_exclusive_utc"])
    files = discover_sources(Path(source["job_directory"]), start, end)
    daily_frames: list[pd.DataFrame] = []
    reused = built = 0
    for index, path in enumerate(files, start=1):
        destination = daily_root / path.name.replace(".dbn.zst", ".auction.parquet")
        if destination.exists() and not force:
            day = pd.read_parquet(destination)
            reused += 1
        else:
            day = aggregate_session(load_dbn_trades(path), config["auction"])
            day.to_parquet(destination, index=False)
            built += 1
        if not day.empty:
            daily_frames.append(day)
        if index % 50 == 0:
            print(json.dumps({"processed": index, "total": len(files), "built": built, "reused": reused}), flush=True)
    frame = pd.concat(daily_frames, ignore_index=True).sort_values("available_time_utc")
    sessions = (
        frame[["session_date", "session_poc", "session_value_low", "session_value_high"]]
        .drop_duplicates("session_date")
        .sort_values("session_date")
    )
    for column in ("session_poc", "session_value_low", "session_value_high"):
        sessions[f"prior_{column}"] = sessions[column].shift(1)
    frame = frame.merge(
        sessions[[
            "session_date",
            "prior_session_poc",
            "prior_session_value_low",
            "prior_session_value_high",
        ]],
        on="session_date",
        how="left",
        validate="many_to_one",
    )
    baseline = int(config["auction"]["volume_baseline_sessions"])
    frame = frame.sort_values(["session_bar_index", "session_date"])
    frame["prior_cumulative_volume_median"] = frame.groupby(
        "session_bar_index", observed=True
    )["cumulative_volume"].transform(
        lambda values: values.shift(1).rolling(baseline, min_periods=baseline).median()
    )
    frame["cumulative_volume_ratio"] = (
        frame["cumulative_volume"] / frame["prior_cumulative_volume_median"].replace(0.0, np.nan)
    )
    frame = frame.sort_values("available_time_utc").reset_index(drop=True)
    frame.to_parquet(output, index=False)
    evidence = {
        "cache": str(output),
        "cache_sha256": sha256_file(output),
        "rows": int(len(frame)),
        "sessions": int(frame["session_date"].nunique()),
        "first_available": frame["available_time_utc"].min().isoformat(),
        "last_available": frame["available_time_utc"].max().isoformat(),
        "source_files": len(files),
        "daily_built": built,
        "daily_reused": reused,
        "download_manifest_sha256": sha256_file(Path(source["download_manifest"])),
    }
    output.with_suffix(".manifest.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return frame, evidence


def load_cache(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(config["comex_source"]["cache"])
    manifest = path.with_suffix(".manifest.json")
    if not path.exists() or not manifest.exists():
        raise FileNotFoundError(f"Auction cache is not built: {path}")
    frame = pd.read_parquet(path)
    evidence = json.loads(manifest.read_text(encoding="utf-8"))
    actual = sha256_file(path)
    if actual != evidence["cache_sha256"]:
        raise ValueError(f"Auction cache hash mismatch: {actual}")
    for column in ("bucket", "available_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    if frame["available_time_utc"].duplicated().any():
        raise ValueError("Auction cache contains duplicate availability timestamps")
    if not (frame["available_time_utc"] > frame["bucket"]).all():
        raise ValueError("Auction rows must be available strictly after their buckets")
    return frame.sort_values("available_time_utc").reset_index(drop=True), evidence


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def spot_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    prior = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - prior).abs(),
            (frame["mid_low"] - prior).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def prepare_joined(spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    spot = spot_m5.copy()
    spot["spot_atr"] = spot_atr(spot, int(config["signal"]["spot_atr_period"]))
    joined = spot.merge(
        auction_m5,
        left_on="timestamp_utc",
        right_on="available_time_utc",
        how="inner",
        validate="one_to_one",
        suffixes=("_spot", "_futures"),
    )
    joined = joined.sort_values(["session_date", "available_time_utc"]).reset_index(drop=True)
    return joined


def _candidate_rows(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    family: str,
    config: dict[str, Any],
) -> pd.DataFrame:
    selected = frame.loc[mask & direction.ne(0)].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["available_time_utc"]
    selected["atr_value"] = selected["spot_atr"]
    family_config = config["families"][family]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"] * float(family_config["stop_atr"]) * selected["spot_atr"]
    )
    selected["target_r"] = float(family_config["target_r"])
    selected["maximum_hold_hours"] = float(family_config["maximum_hold_hours"])
    selected = selected.drop_duplicates(["session_date", "direction"], keep="first")
    columns = [
        "family_id",
        "signal_time",
        "session_date",
        "direction",
        "direction_sign",
        "stop_frozen",
        "atr_value",
        "target_r",
        "maximum_hold_hours",
        "close",
        "running_poc",
        "prior_session_poc",
        "prior_session_value_low",
        "prior_session_value_high",
        "cumulative_delta_ratio",
        "cumulative_volume_ratio",
    ]
    return selected[columns]


def generate_candidates(
    spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    frame = prepare_joined(spot_m5, auction_m5, config)
    signal = config["signal"]
    atr = frame["spot_atr"]
    high_boundary = frame["prior_session_value_high"]
    low_boundary = frame["prior_session_value_low"]
    local_time = frame["available_local_time"]
    accepted_high = frame["close"] > high_boundary + float(signal["acceptance_boundary_buffer_atr"]) * atr
    accepted_low = frame["close"] < low_boundary - float(signal["acceptance_boundary_buffer_atr"]) * atr
    for shift in range(1, int(signal["acceptance_bars"])):
        same = frame["session_date"].eq(frame["session_date"].shift(shift))
        accepted_high &= same & (frame["close"].shift(shift) > high_boundary.shift(shift))
        accepted_low &= same & (frame["close"].shift(shift) < low_boundary.shift(shift))
    acceptance_direction = pd.Series(
        np.select([accepted_high, accepted_low], [1, -1], default=0), index=frame.index
    )
    extension = np.where(
        acceptance_direction > 0,
        (frame["close"] - high_boundary) / atr,
        (low_boundary - frame["close"]) / atr,
    )
    acceptance_mask = (
        local_time.between(signal["acceptance_start_local"], signal["acceptance_end_local"])
        & np.isfinite(atr)
        & (extension <= float(signal["acceptance_maximum_extension_atr"]))
        & (
            acceptance_direction * frame["cumulative_delta_ratio"]
            >= float(signal["acceptance_minimum_directional_delta_ratio"])
        )
    )

    high_failure = (
        (frame["high"] >= high_boundary + float(signal["failed_auction_minimum_excursion_atr"]) * atr)
        & (frame["close"] <= high_boundary - float(signal["failed_auction_minimum_reentry_atr"]) * atr)
        & (frame["close"] < frame["open"])
    )
    low_failure = (
        (frame["low"] <= low_boundary - float(signal["failed_auction_minimum_excursion_atr"]) * atr)
        & (frame["close"] >= low_boundary + float(signal["failed_auction_minimum_reentry_atr"]) * atr)
        & (frame["close"] > frame["open"])
    )
    failed_direction = pd.Series(
        np.select([high_failure, low_failure], [-1, 1], default=0), index=frame.index
    )
    failed_mask = local_time.between(
        signal["failed_auction_start_local"], signal["failed_auction_end_local"]
    ) & np.isfinite(atr)

    opening_high = (
        (frame["running_poc"] >= high_boundary + float(signal["opening_minimum_poc_migration_atr"]) * atr)
        & (frame["close"] >= high_boundary + float(signal["opening_minimum_close_extension_atr"]) * atr)
    )
    opening_low = (
        (frame["running_poc"] <= low_boundary - float(signal["opening_minimum_poc_migration_atr"]) * atr)
        & (frame["close"] <= low_boundary - float(signal["opening_minimum_close_extension_atr"]) * atr)
    )
    opening_direction = pd.Series(
        np.select([opening_high, opening_low], [1, -1], default=0), index=frame.index
    )
    opening_mask = (
        local_time.eq(signal["opening_signal_local"])
        & np.isfinite(atr)
        & (
            opening_direction * frame["cumulative_delta_ratio"]
            >= float(signal["opening_minimum_directional_delta_ratio"])
        )
        & (frame["cumulative_volume_ratio"] >= float(signal["opening_minimum_volume_ratio"]))
    )
    candidates = pd.concat(
        [
            _candidate_rows(frame, acceptance_mask, acceptance_direction, ACCEPTANCE, config),
            _candidate_rows(frame, failed_mask, failed_direction, FAILED_AUCTION, config),
            _candidate_rows(frame, opening_mask, opening_direction, OPENING_MIGRATION, config),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "family_id",
                "signal_time",
                "session_date",
                "direction",
                "direction_sign",
                "stop_frozen",
                "atr_value",
                "target_r",
                "maximum_hold_hours",
            ]
        )
    return candidates.sort_values(["signal_time", "family_id"], kind="mergesort").reset_index(drop=True)
