from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

import numpy as np
import pandas as pd


FORBIDDEN_OUTPUT_TOKENS = (
    "future",
    "label",
    "target",
    "pnl",
    "profit",
    "direction",
    "signal",
    "trade",
)


def load_config(root: Path) -> dict[str, Any]:
    path = root / "config" / "histdata_xauusd_independent_feed_audit_v47.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source(path: Path, expected_sha256: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ValueError(f"Source hash mismatch for {path}: {actual}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def parse_histdata_timestamp(values: pd.Series, utc_offset_hours: int) -> pd.Series:
    parsed = pd.to_datetime(values, format="%Y%m%d %H%M%S%f", errors="raise")
    return (parsed + pd.Timedelta(hours=utc_offset_hours)).dt.tz_localize("UTC")


def load_histdata_ticks(
    csv_path: Path, utc_offset_hours: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = pd.read_csv(
        csv_path,
        header=None,
        names=["timestamp_est", "bid", "ask", "volume"],
        dtype={"timestamp_est": "string", "bid": "float64", "ask": "float64"},
    )
    if list(frame.columns) != ["timestamp_est", "bid", "ask", "volume"]:
        raise ValueError("Unexpected HistData schema")

    timestamps = parse_histdata_timestamp(frame.pop("timestamp_est"), utc_offset_hours)
    monotonic = bool(timestamps.is_monotonic_increasing)
    duplicate_timestamps = int(timestamps.duplicated().sum())
    exact_duplicates = int(
        pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "bid": frame["bid"],
                "ask": frame["ask"],
            }
        )
        .duplicated()
        .sum()
    )
    invalid_nonpositive = int(((frame["bid"] <= 0) | (frame["ask"] <= 0)).sum())
    crossed = int((frame["ask"] < frame["bid"]).sum())
    spread = frame["ask"] - frame["bid"]

    ticks = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "bid": frame["bid"].to_numpy(),
            "ask": frame["ask"].to_numpy(),
        }
    )
    ticks["mid"] = (ticks["bid"] + ticks["ask"]) / 2.0
    ticks["spread"] = ticks["ask"] - ticks["bid"]

    span = timestamps.iloc[-1] - timestamps.iloc[0]
    audit = {
        "rows": int(len(ticks)),
        "first_timestamp_utc": timestamps.iloc[0].isoformat(),
        "last_timestamp_utc": timestamps.iloc[-1].isoformat(),
        "calendar_days_spanned": int(span.total_seconds() // 86400) + 1,
        "timestamps_monotonic": monotonic,
        "duplicate_timestamp_rows": duplicate_timestamps,
        "exact_duplicate_rows": exact_duplicates,
        "nonpositive_quote_rows": invalid_nonpositive,
        "crossed_quote_rows": crossed,
        "median_spread_dollars": float(spread.median()),
        "spread_p99_dollars": float(spread.quantile(0.99)),
        "maximum_spread_dollars": float(spread.max()),
    }
    return ticks, audit


def aggregate_histdata_m5(ticks: pd.DataFrame) -> pd.DataFrame:
    indexed = ticks.set_index("timestamp_utc")
    bars = indexed.resample("5min", origin="epoch").agg(
        bid_close=("bid", "last"),
        ask_close=("ask", "last"),
        mid_close=("mid", "last"),
        spread_median=("spread", "median"),
        spread_max=("spread", "max"),
        tick_count=("mid", "size"),
    )
    bars = bars.loc[bars["tick_count"] > 0].reset_index()
    bars = bars.rename(columns={"timestamp_utc": "bar_start_utc"})
    bars["available_time_utc"] = bars["bar_start_utc"] + pd.Timedelta(minutes=5)
    return bars


def load_dukascopy_m5(
    path: Path, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    columns = ["timestamp_ms", "bid_close", "ask_close", "mid_close", "xau_tick_count"]
    frame = pd.read_parquet(path, columns=columns)
    frame["bar_start_utc"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame = frame.loc[
        (frame["bar_start_utc"] >= start) & (frame["bar_start_utc"] < end)
    ].copy()
    frame["available_time_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    return frame.drop(columns=["timestamp_ms"])


def compare_m5_feeds(
    histdata: pd.DataFrame, dukascopy: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    merged = histdata.merge(
        dukascopy,
        on=["bar_start_utc", "available_time_utc"],
        how="inner",
        suffixes=("_histdata", "_dukascopy"),
        validate="one_to_one",
    ).sort_values("bar_start_utc")
    if merged.empty:
        raise ValueError("No contemporaneous HistData/Dukascopy M5 overlap")

    merged["mid_basis_dollars"] = (
        merged["mid_close_histdata"] - merged["mid_close_dukascopy"]
    )
    continuity = merged["bar_start_utc"].diff().eq(pd.Timedelta(minutes=5))
    hist_change = merged["mid_close_histdata"].diff()
    duk_change = merged["mid_close_dukascopy"].diff()
    return_mask = continuity & hist_change.notna() & duk_change.notna()
    contemporaneous_correlation = float(
        hist_change.loc[return_mask].corr(duk_change.loc[return_mask])
    )
    exact_close = np.isclose(
        merged["mid_close_histdata"],
        merged["mid_close_dukascopy"],
        rtol=0.0,
        atol=0.0005,
    )

    active_dukascopy = int(len(dukascopy))
    comparison = {
        "histdata_active_m5_bars": int(len(histdata)),
        "dukascopy_active_m5_bars": active_dukascopy,
        "matched_m5_bars": int(len(merged)),
        "active_bar_coverage_fraction": (
            float(len(merged) / active_dukascopy) if active_dukascopy else 0.0
        ),
        "consecutive_return_pairs": int(return_mask.sum()),
        "contemporaneous_return_correlation": contemporaneous_correlation,
        "median_basis_dollars": float(merged["mid_basis_dollars"].median()),
        "median_absolute_basis_dollars": float(
            merged["mid_basis_dollars"].abs().median()
        ),
        "basis_standard_deviation_dollars": float(
            merged["mid_basis_dollars"].std(ddof=1)
        ),
        "exact_mid_close_fraction": float(exact_close.mean()),
    }

    daily = (
        merged.assign(date_utc=merged["bar_start_utc"].dt.date.astype(str))
        .groupby("date_utc", as_index=False)
        .agg(
            matched_bars=("bar_start_utc", "size"),
            histdata_ticks=("tick_count", "sum"),
            dukascopy_ticks=("xau_tick_count", "sum"),
            median_basis_dollars=("mid_basis_dollars", "median"),
            maximum_absolute_basis_dollars=(
                "mid_basis_dollars",
                lambda values: float(values.abs().max()),
            ),
            median_histdata_spread_dollars=("spread_median", "median"),
        )
    )
    return merged, comparison, daily


def parse_status_report(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    gaps = [int(value) for value in re.findall(r"Gap of (\d+)s", text)]
    average_match = re.search(r"Average tick interval: (\d+) miliseconds", text)
    maximum_match = re.search(r"Maximum tick interval found: (\d+) miliseconds", text)
    return {
        "reported_gap_count": len(gaps),
        "reported_gaps_at_least_60_seconds": int(sum(value >= 60 for value in gaps)),
        "reported_gaps_at_least_3500_seconds": int(
            sum(value >= 3500 for value in gaps)
        ),
        "reported_average_tick_interval_ms": (
            int(average_match.group(1)) if average_match else None
        ),
        "reported_maximum_tick_interval_ms": (
            int(maximum_match.group(1)) if maximum_match else None
        ),
    }


def evaluate_gates(
    source: Mapping[str, Any], comparison: Mapping[str, Any], gates: Mapping[str, Any]
) -> dict[str, bool]:
    invalid_rows = int(source["nonpositive_quote_rows"]) + int(
        source["crossed_quote_rows"]
    )
    return {
        "minimum_rows": int(source["rows"]) >= int(gates["minimum_rows"]),
        "minimum_calendar_days_spanned": int(source["calendar_days_spanned"])
        >= int(gates["minimum_calendar_days_spanned"]),
        "timestamps_monotonic": bool(source["timestamps_monotonic"]),
        "maximum_invalid_quote_rows": invalid_rows
        <= int(gates["maximum_invalid_quote_rows"]),
        "positive_median_spread": float(source["median_spread_dollars"]) > 0.0,
        "maximum_spread_p99_dollars": float(source["spread_p99_dollars"])
        <= float(gates["maximum_spread_p99_dollars"]),
        "minimum_active_bar_coverage_fraction": float(
            comparison["active_bar_coverage_fraction"]
        )
        >= float(gates["minimum_active_bar_coverage_fraction"]),
        "minimum_matched_bars": int(comparison["matched_m5_bars"])
        >= int(gates["minimum_matched_bars"]),
        "minimum_contemporaneous_return_correlation": float(
            comparison["contemporaneous_return_correlation"]
        )
        >= float(gates["minimum_contemporaneous_return_correlation"]),
        "maximum_median_absolute_basis_dollars": float(
            comparison["median_absolute_basis_dollars"]
        )
        <= float(gates["maximum_median_absolute_basis_dollars"]),
        "maximum_exact_mid_close_fraction": float(
            comparison["exact_mid_close_fraction"]
        )
        < float(gates["maximum_exact_mid_close_fraction"]),
        "minimum_basis_standard_deviation_dollars": float(
            comparison["basis_standard_deviation_dollars"]
        )
        > float(gates["minimum_basis_standard_deviation_dollars"]),
    }


def forbidden_columns(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in frame.columns
        if any(token in column.lower() for token in FORBIDDEN_OUTPUT_TOKENS)
    ]


def run_audit(config: Mapping[str, Any]) -> dict[str, Any]:
    hist_config = config["histdata"]
    dukas_config = config["dukascopy"]
    source_files = {
        "histdata_archive": verify_source(
            Path(hist_config["archive_path"]), hist_config["archive_sha256"]
        ),
        "histdata_csv": verify_source(
            Path(hist_config["csv_path"]), hist_config["csv_sha256"]
        ),
        "histdata_status": verify_source(
            Path(hist_config["status_path"]), hist_config["status_sha256"]
        ),
        "dukascopy_m5": verify_source(
            Path(dukas_config["m5_path"]), dukas_config["m5_sha256"]
        ),
    }

    ticks, source_audit = load_histdata_ticks(
        Path(hist_config["csv_path"]), int(hist_config["fixed_est_to_utc_hours"])
    )
    hist_m5 = aggregate_histdata_m5(ticks)
    start = pd.Timestamp(config["window"]["start_inclusive_utc"])
    end = pd.Timestamp(config["window"]["end_exclusive_utc"])
    dukas_m5 = load_dukascopy_m5(Path(dukas_config["m5_path"]), start, end)
    _, comparison, daily = compare_m5_feeds(hist_m5, dukas_m5)
    status_audit = parse_status_report(Path(hist_config["status_path"]))
    gates = evaluate_gates(source_audit, comparison, config["gates"])

    forbidden = forbidden_columns(hist_m5)
    if forbidden:
        raise ValueError(f"Forbidden output columns: {forbidden}")
    all_pass = all(gates.values())
    result = {
        "schema_version": config["schema_version"],
        "decision": (
            "ACCEPT_FOR_SEPARATELY_PREREGISTERED_FEATURE_RESEARCH"
            if all_pass
            else "REJECT_SOURCE_FOR_CROSSVENUE_RESEARCH"
        ),
        "source_files": source_files,
        "histdata_source_audit": source_audit,
        "histdata_status_report": status_audit,
        "crossvenue_comparison": comparison,
        "gates": gates,
        "all_gates_pass": all_pass,
        "execution_authorized": False,
        "strategy_research_authorized_in_v47": False,
    }
    return {"result": result, "histdata_m5": hist_m5, "daily": daily}
