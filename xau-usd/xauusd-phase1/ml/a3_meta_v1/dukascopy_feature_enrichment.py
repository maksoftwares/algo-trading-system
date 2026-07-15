from __future__ import annotations

import bisect
import hashlib
import json
import math
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any


DUKASCOPY_NUMERIC_FEATURES = (
    "duka_spread_last_bps",
    "duka_spread_p95_60m_bps",
    "duka_spread_last_to_median_60m",
    "duka_tick_count_5m_log1p",
    "duka_tick_count_60m_log1p",
    "duka_mid_return_5m",
    "duka_mid_return_60m",
    "duka_realized_vol_60m_bps",
)


class FeatureUnavailableError(ValueError):
    pass


def enrich_rows_with_dukascopy_features(
    root: Path, rows: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    storage_root, symbol, coverage_start, coverage_end = _validate_config(root, config)
    decode_payload = _load_decoder(root)
    raw_cache: dict[Path, tuple[list[Any], str]] = {}
    manifest_cache: dict[Path, dict[str, Any]] = {}
    source_hashes: dict[str, str] = {}
    tick_counts: list[int] = []
    audit_rows: list[dict[str, Any]] = []
    enriched_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []

    for row in rows:
        entry = _parse_utc(str(row["entry_time"]))
        if not coverage_start <= entry < coverage_end:
            raise ValueError(f"Dukascopy entry {entry.isoformat()} is outside declared coverage")
        try:
            ticks = _load_window(
                storage_root,
                symbol,
                entry,
                decode_payload,
                raw_cache,
                manifest_cache,
                source_hashes,
            )
            features, tick_count = _features_for_entry(ticks, entry)
        except FeatureUnavailableError as exc:
            exclusions.append({"entry_time": str(row["entry_time"]), "reason": str(exc)})
            continue
        row.update(features)
        enriched_rows.append(row)
        tick_counts.append(tick_count)
        audit_rows.append(
            {
                "split": row["split"],
                "strategy_family": row["strategy_family"],
                "direction": row["direction"],
                "entry_time": row["entry_time"],
                **features,
            }
        )

    composite_source = "".join(f"{path}|{digest}\n" for path, digest in sorted(source_hashes.items()))
    feature_bytes = (json.dumps(audit_rows, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    audit = {
        "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
        "symbol": symbol,
        "storage_root": "${" + str(config["storage_environment_variable"]) + "}",
        "coverage_start_utc": _iso(coverage_start),
        "coverage_end_exclusive_utc": _iso(coverage_end),
        "strictly_before_entry": True,
        "lookback_minutes": 60,
        "pre_roll_minutes": 5,
        "feature_names": list(DUKASCOPY_NUMERIC_FEATURES),
        "input_rows": len(rows),
        "enriched_rows": len(enriched_rows),
        "excluded_unavailable_rows": len(exclusions),
        "exclusions": exclusions,
        "source_hour_files": len(source_hashes),
        "source_hour_files_sha256": hashlib.sha256(composite_source.encode("utf-8")).hexdigest(),
        "feature_rows_sha256": hashlib.sha256(feature_bytes).hexdigest(),
        "minimum_ticks_60m": min(tick_counts) if tick_counts else 0,
        "median_ticks_60m": median(tick_counts) if tick_counts else 0,
        "maximum_ticks_60m": max(tick_counts) if tick_counts else 0,
        "missing_rows": 0,
        "future_ticks_used": 0,
    }
    return enriched_rows, audit


def filter_rows_to_dukascopy_availability(
    root: Path, rows: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filtered, audit = enrich_rows_with_dukascopy_features(root, rows, config)
    for row in filtered:
        for feature in DUKASCOPY_NUMERIC_FEATURES:
            row.pop(feature, None)
    audit = {**audit, "mode": "AVAILABILITY_FILTER_ONLY"}
    return filtered, audit


def _validate_config(
    root: Path, config: dict[str, Any]
) -> tuple[Path, str, datetime, datetime]:
    if config.get("source") != "OFFICIAL_DUKASCOPY_JETTA_V1":
        raise ValueError("Dukascopy feature source must be OFFICIAL_DUKASCOPY_JETTA_V1")
    if config.get("strictly_before_entry") is not True:
        raise ValueError("Dukascopy features require strictly_before_entry=true")
    if config.get("exclude_unavailable_rows") is not True:
        raise ValueError("Dukascopy features require exclude_unavailable_rows=true")
    if int(config.get("lookback_minutes", 0)) != 60 or int(config.get("pre_roll_minutes", 0)) != 5:
        raise ValueError("Dukascopy feature window is frozen at 60 minutes plus 5 minutes of pre-roll")
    env_name = str(config.get("storage_environment_variable", "")).strip()
    raw_root = os.environ.get(env_name, "").strip()
    if not env_name or not raw_root:
        raise ValueError(f"{env_name or 'Dukascopy storage environment variable'} is not set")
    storage_root = Path(raw_root).resolve()
    repo_root = root.resolve().parents[1]
    if storage_root == repo_root or repo_root in storage_root.parents:
        raise ValueError("Dukascopy storage must remain outside the repository")
    if not (storage_root / "raw" / "XAUUSD").is_dir():
        raise ValueError("Dukascopy XAUUSD raw storage is missing")
    symbol = str(config.get("symbol", ""))
    if symbol != "XAUUSD":
        raise ValueError("this feature contract is frozen to XAUUSD")
    coverage_start = _parse_utc(str(config["coverage_start_utc"]))
    coverage_end = _parse_utc(str(config["coverage_end_exclusive_utc"]))
    if coverage_start >= coverage_end:
        raise ValueError("Dukascopy coverage interval is invalid")
    return storage_root, symbol, coverage_start, coverage_end


def _load_decoder(root: Path) -> Any:
    repo_root = root.resolve().parents[1]
    source_root = (
        repo_root
        / "multi-asset"
        / "data-foundation"
        / "dukascopy-ticks-v1"
        / "src"
    )
    if not source_root.is_dir():
        raise ValueError("validated Dukascopy foundation source is missing")
    source_text = str(source_root)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)
    from dukascopy_tick_foundation.foundation import decode_payload

    return decode_payload


def _load_window(
    storage_root: Path,
    symbol: str,
    entry: datetime,
    decode_payload: Any,
    raw_cache: dict[Path, tuple[list[Any], str]],
    manifest_cache: dict[Path, dict[str, Any]],
    source_hashes: dict[str, str],
) -> list[Any]:
    start = entry - timedelta(minutes=65)
    first_hour = start.replace(minute=0, second=0, microsecond=0)
    last_included = entry - timedelta(microseconds=1)
    last_hour = last_included.replace(minute=0, second=0, microsecond=0)
    ticks: list[Any] = []
    hour = first_hour
    while hour <= last_hour:
        path = (
            storage_root
            / "raw"
            / symbol
            / f"year={hour.year:04d}"
            / f"month={hour.month:02d}"
            / f"{hour:%Y%m%d%H}.json"
        )
        hour_ticks, digest = _load_hour(
            storage_root, symbol, hour, path, decode_payload, raw_cache, manifest_cache
        )
        relative = path.relative_to(storage_root).as_posix()
        source_hashes[relative] = digest
        ticks.extend(hour_ticks)
        hour += timedelta(hours=1)
    start_ms = int(start.timestamp() * 1000)
    entry_ms = int(entry.timestamp() * 1000)
    selected = [tick for tick in ticks if start_ms <= tick.timestamp_ms < entry_ms]
    if not selected:
        raise FeatureUnavailableError(f"no causal Dukascopy ticks before {entry.isoformat()}")
    return selected


def _load_hour(
    storage_root: Path,
    symbol: str,
    hour: datetime,
    path: Path,
    decode_payload: Any,
    raw_cache: dict[Path, tuple[list[Any], str]],
    manifest_cache: dict[Path, dict[str, Any]],
) -> tuple[list[Any], str]:
    if path in raw_cache:
        return raw_cache[path]
    if not path.is_file():
        raise ValueError(f"missing Dukascopy raw hour: {path}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    manifest_path = path.parent / "_ACQUISITION_MANIFEST.json"
    if manifest_path not in manifest_cache:
        if not manifest_path.is_file():
            raise ValueError(f"missing Dukascopy acquisition manifest: {manifest_path}")
        manifest_cache[manifest_path] = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = manifest_cache[manifest_path]
    relative = path.relative_to(storage_root).as_posix()
    matching = [item for item in manifest.get("rows", []) if item.get("path") == relative]
    if len(matching) != 1 or matching[0].get("sha256") != digest:
        raise ValueError(f"Dukascopy raw hour does not match its frozen manifest: {path}")
    if matching[0].get("status") not in {"DOWNLOADED_VALID", "RESUMED_VALID"}:
        raise ValueError(f"Dukascopy raw hour is not validated: {path}")
    source_file_id = f"{symbol}-{hour:%Y%m%d%H}"
    decoded = decode_payload(raw, symbol, source_file_id)
    hour_start_ms = int(hour.timestamp() * 1000)
    if any(not hour_start_ms <= tick.timestamp_ms < hour_start_ms + 3_600_000 for tick in decoded):
        raise ValueError(f"Dukascopy decoded tick escaped its UTC hour: {path}")
    raw_cache[path] = (decoded, digest)
    return raw_cache[path]


def _features_for_entry(ticks: list[Any], entry: datetime) -> tuple[dict[str, float], int]:
    entry_ms = int(entry.timestamp() * 1000)
    start_60 = entry_ms - 3_600_000
    start_5 = entry_ms - 300_000
    timestamps = [tick.timestamp_ms for tick in ticks]
    analysis = [tick for tick in ticks if start_60 <= tick.timestamp_ms < entry_ms]
    recent = [tick for tick in analysis if tick.timestamp_ms >= start_5]
    if len(analysis) < 10 or not recent:
        raise FeatureUnavailableError(f"insufficient Dukascopy ticks before {entry.isoformat()}")

    def mid(tick: Any) -> float:
        return (float(tick.bid) + float(tick.ask)) / 2.0

    def asof_mid(cutoff_ms: int) -> float:
        index = bisect.bisect_right(timestamps, cutoff_ms) - 1
        if index < 0:
            raise FeatureUnavailableError(f"Dukascopy pre-roll is insufficient before {entry.isoformat()}")
        return mid(ticks[index])

    last = analysis[-1]
    last_mid = mid(last)
    spreads_bps = [(float(tick.ask) - float(tick.bid)) / mid(tick) * 10_000.0 for tick in analysis]
    median_spread = median(spreads_bps)
    if median_spread <= 0.0:
        raise ValueError("Dukascopy median spread must be positive")
    minute_closes: dict[int, float] = {}
    for tick in analysis:
        minute_closes[tick.timestamp_ms // 60_000] = mid(tick)
    closes = [minute_closes[key] for key in sorted(minute_closes)]
    if len(closes) < 10:
        raise FeatureUnavailableError(f"insufficient Dukascopy minute observations before {entry.isoformat()}")
    realized_variance = sum(math.log(current / previous) ** 2 for previous, current in zip(closes, closes[1:]))
    features = {
        "duka_spread_last_bps": spreads_bps[-1],
        "duka_spread_p95_60m_bps": _percentile(spreads_bps, 0.95),
        "duka_spread_last_to_median_60m": spreads_bps[-1] / median_spread,
        "duka_tick_count_5m_log1p": math.log1p(len(recent)),
        "duka_tick_count_60m_log1p": math.log1p(len(analysis)),
        "duka_mid_return_5m": last_mid / asof_mid(start_5) - 1.0,
        "duka_mid_return_60m": last_mid / asof_mid(start_60) - 1.0,
        "duka_realized_vol_60m_bps": math.sqrt(realized_variance) * 10_000.0,
    }
    if any(not math.isfinite(value) for value in features.values()):
        raise ValueError(f"non-finite Dukascopy feature before {entry.isoformat()}")
    return features, len(analysis)


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
