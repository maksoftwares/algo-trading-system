from __future__ import annotations

import hashlib
import io
import json
import os
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


DEFAULT_CONTRACT = Path("config/ml/a3_ml_macro_futures_foundation_v1.json")
USER_AGENT = "xau-research-foundation/1.0"


class MacroFuturesFoundationError(RuntimeError):
    pass


def run_macro_futures_foundation(
    root: Path,
    contract_path: Path | None = None,
    *,
    refresh_sources: bool = False,
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _storage_root(contract)
    outputs = _external_outputs(storage_root, contract)
    outputs["source_directory"].mkdir(parents=True, exist_ok=True)

    source_rows: list[dict[str, Any]] = []
    fred_frames: list[pd.DataFrame] = []
    for series in contract["fred_series"]:
        destination = outputs["source_directory"] / f"fred_{series['series_id']}.csv"
        metadata = _acquire(str(series["url"]), destination, refresh_sources)
        source_rows.append({**metadata, "source_kind": "FRED", "source_id": series["series_id"]})
        fred_frames.append(_read_fred(destination, series))

    cftc_frames: list[pd.DataFrame] = []
    cftc = contract["cftc"]
    for year in cftc["years"]:
        url = str(cftc["url_template"]).format(year=int(year))
        destination = outputs["source_directory"] / f"cftc_disaggregated_futures_{year}.zip"
        metadata = _acquire(url, destination, refresh_sources)
        source_rows.append({**metadata, "source_kind": "CFTC", "source_id": str(year)})
        cftc_frames.append(_read_cftc(destination, cftc))

    fred = _combine_fred(fred_frames)
    positioning = _combine_cftc(cftc_frames)
    daily = _build_daily_features(fred, positioning)
    start = pd.Timestamp(contract["research_window"]["start_utc"])
    end = pd.Timestamp(contract["research_window"]["end_exclusive_utc"])
    daily = daily[(daily["available_at_utc"] >= start) & (daily["available_at_utc"] < end)].copy()
    _validate_daily_features(daily, start, end)
    daily.to_parquet(outputs["daily_features_parquet"], index=False)

    base_cache = storage_root / str(contract["base_feature_cache"]["relative_path"])
    if not base_cache.is_file():
        raise MacroFuturesFoundationError(f"base feature cache is missing: {base_cache}")
    if _sha256_file(base_cache) != str(contract["base_feature_cache"]["sha256"]):
        raise MacroFuturesFoundationError("base feature cache hash mismatch")
    market = pd.read_parquet(base_cache)
    enriched = _asof_join_market(market, daily)
    _validate_enriched(enriched)
    enriched.to_parquet(outputs["enriched_m5_parquet"], index=False)

    source_rows.sort(key=lambda row: (row["source_kind"], row["source_id"]))
    manifest = {
        "schema_version": contract["schema_version"],
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "availability_policy": {
            "treasury_series": "observation date plus one calendar day at 00:00 UTC",
            "broad_usd_index": "observation date plus seven calendar days at 00:00 UTC",
            "cftc_gold": "Tuesday report date plus three days at 21:00 UTC",
        },
        "licensed_inputs_not_present": [
            "COMEX intraday trades",
            "COMEX market depth or order book",
            "consensus macro forecasts",
            "ICE US Dollar Index intraday history",
        ],
        "sources": source_rows,
        "source_inventory_sha256": _canonical_sha256(source_rows),
        "daily_features": _artifact(outputs["daily_features_parquet"], len(daily)),
        "enriched_m5": _artifact(outputs["enriched_m5_parquet"], len(enriched)),
        "coverage": {
            "first_market_timestamp_utc": _utc_iso_from_ms(int(enriched["timestamp_ms"].min())),
            "last_market_timestamp_utc": _utc_iso_from_ms(int(enriched["timestamp_ms"].max())),
            "first_macro_availability_utc": daily["available_at_utc"].min().isoformat().replace("+00:00", "Z"),
            "last_macro_availability_utc": daily["available_at_utc"].max().isoformat().replace("+00:00", "Z"),
            "macro_joined_market_rows": int(enriched["macro_available_at_ms"].notna().sum()),
            "cot_joined_market_rows": int(enriched["cot_available_at_ms"].notna().sum()),
        },
        "causality_checks": {
            "macro_availability_not_after_market": True,
            "cot_availability_not_after_market": True,
            "unique_daily_availability": True,
            "base_feature_cache_hash_verified": True,
        },
    }
    outputs["manifest_json"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = root / str(contract["report_output"])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({**manifest, "external_manifest": str(outputs["manifest_json"])}, indent=2), encoding="utf-8")
    return report


def _validate_contract(contract: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "storage_environment_variable",
        "research_window",
        "base_feature_cache",
        "fred_series",
        "cftc",
        "external_outputs",
        "report_output",
    }
    missing = sorted(required - set(contract))
    if missing:
        raise MacroFuturesFoundationError(f"contract fields missing: {missing}")
    columns = [str(row["column"]) for row in contract["fred_series"]]
    if len(columns) != len(set(columns)):
        raise MacroFuturesFoundationError("FRED output columns must be unique")


def _storage_root(contract: Mapping[str, Any]) -> Path:
    variable = str(contract["storage_environment_variable"])
    raw = os.environ.get(variable, "").strip()
    if not raw:
        raise MacroFuturesFoundationError(f"{variable} is required")
    path = Path(raw).resolve()
    if not path.is_dir():
        raise MacroFuturesFoundationError(f"storage root does not exist: {path}")
    return path


def _external_outputs(storage_root: Path, contract: Mapping[str, Any]) -> dict[str, Path]:
    spec = contract["external_outputs"]
    base = storage_root / str(spec["relative_root"])
    base.mkdir(parents=True, exist_ok=True)
    return {
        "source_directory": base / str(spec["source_directory"]),
        "daily_features_parquet": base / str(spec["daily_features_parquet"]),
        "enriched_m5_parquet": base / str(spec["enriched_m5_parquet"]),
        "manifest_json": base / str(spec["manifest_json"]),
    }


def _acquire(url: str, destination: Path, refresh: bool) -> dict[str, Any]:
    if refresh or not destination.is_file():
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read()
        except Exception as exc:
            raise MacroFuturesFoundationError(f"download failed for {url}: {exc}") from exc
        if not payload:
            raise MacroFuturesFoundationError(f"empty download from {url}")
        destination.write_bytes(payload)
    return {
        "url": url,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": _sha256_file(destination),
    }


def _read_fred(path: Path, spec: Mapping[str, Any]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    date_column = "observation_date" if "observation_date" in frame.columns else "DATE"
    value_columns = [column for column in frame.columns if column != date_column]
    if len(value_columns) != 1:
        raise MacroFuturesFoundationError(f"unexpected FRED schema for {spec['series_id']}")
    result = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(frame[date_column], utc=True, errors="coerce"),
            str(spec["column"]): pd.to_numeric(frame[value_columns[0]], errors="coerce"),
        }
    ).dropna()
    lag = int(spec["availability_lag_days"])
    result["available_at_utc"] = result["observation_date"] + pd.Timedelta(days=lag)
    return result[["available_at_utc", str(spec["column"])]]


def _combine_fred(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        raise MacroFuturesFoundationError("no FRED frames")
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="available_at_utc", how="outer", validate="one_to_one")
    return merged.sort_values("available_at_utc").reset_index(drop=True)


def _read_cftc(path: Path, spec: Mapping[str, Any]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise MacroFuturesFoundationError(f"unexpected CFTC archive contents: {names}")
        payload = archive.read(names[0])
    frame = pd.read_csv(io.BytesIO(payload), low_memory=False, dtype={"CFTC_Contract_Market_Code": str})
    code = str(spec["contract_market_code"])
    frame["CFTC_Contract_Market_Code"] = frame["CFTC_Contract_Market_Code"].str.strip()
    frame = frame[frame["CFTC_Contract_Market_Code"] == code].copy()
    if frame.empty:
        raise MacroFuturesFoundationError(f"CFTC gold contract {code} missing from {path.name}")
    report_date = pd.to_datetime(frame["Report_Date_as_YYYY-MM-DD"], utc=True, errors="raise")
    frame["available_at_utc"] = (
        report_date
        + pd.Timedelta(days=int(spec["release_delay_days"]))
        + pd.Timedelta(hours=int(spec["conservative_release_hour_utc"]))
    )
    numeric = {
        "Open_Interest_All": "cot_open_interest",
        "M_Money_Positions_Long_All": "cot_managed_money_long",
        "M_Money_Positions_Short_All": "cot_managed_money_short",
        "Prod_Merc_Positions_Long_All": "cot_producer_long",
        "Prod_Merc_Positions_Short_All": "cot_producer_short",
        "Swap_Positions_Long_All": "cot_swap_long",
        "Swap__Positions_Short_All": "cot_swap_short",
    }
    result = frame[["available_at_utc", *numeric]].rename(columns=numeric)
    for column in numeric.values():
        result[column] = pd.to_numeric(result[column], errors="raise")
    if result["available_at_utc"].duplicated().any():
        raise MacroFuturesFoundationError(f"duplicate CFTC gold reports in {path.name}")
    return result.sort_values("available_at_utc").reset_index(drop=True)


def _combine_cftc(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        raise MacroFuturesFoundationError("no CFTC frames")
    result = pd.concat(frames, ignore_index=True).sort_values("available_at_utc")
    if result["available_at_utc"].duplicated().any():
        raise MacroFuturesFoundationError("duplicate CFTC availability timestamps across source years")
    return result.reset_index(drop=True)


def _build_daily_features(fred: pd.DataFrame, cftc: pd.DataFrame) -> pd.DataFrame:
    events = fred.copy().sort_values("available_at_utc")
    value_columns = [column for column in events.columns if column != "available_at_utc"]
    events[value_columns] = events[value_columns].ffill()
    for column in value_columns:
        events[f"{column}_change_1"] = events[column].diff()
        events[f"{column}_change_5"] = events[column].diff(5)
        events[f"{column}_change_20"] = events[column].diff(20)
    events["real_yield_curve_10y_5y"] = events["real_yield_10y"] - events["real_yield_5y"]
    events["nominal_yield_curve_10y_2y"] = events["nominal_yield_10y"] - events["nominal_yield_2y"]
    events["breakeven_inflation_10y"] = events["nominal_yield_10y"] - events["real_yield_10y"]
    events = events.rename(columns={"available_at_utc": "macro_available_at_utc"})

    positions = cftc.copy().sort_values("available_at_utc")
    oi = positions["cot_open_interest"].replace(0, np.nan)
    positions["cot_managed_money_net_share"] = (
        positions["cot_managed_money_long"] - positions["cot_managed_money_short"]
    ) / oi
    positions["cot_producer_net_share"] = (
        positions["cot_producer_long"] - positions["cot_producer_short"]
    ) / oi
    positions["cot_swap_net_share"] = (positions["cot_swap_long"] - positions["cot_swap_short"]) / oi
    for column in ("cot_managed_money_net_share", "cot_producer_net_share", "cot_swap_net_share"):
        positions[f"{column}_change_1"] = positions[column].diff()
        mean = positions[column].rolling(52, min_periods=20).mean()
        std = positions[column].rolling(52, min_periods=20).std(ddof=0).replace(0, np.nan)
        positions[f"{column}_z52"] = (positions[column] - mean) / std
    positions = positions.rename(columns={"available_at_utc": "cot_available_at_utc"})

    timeline = pd.DataFrame(
        {"available_at_utc": sorted(set(events["macro_available_at_utc"]) | set(positions["cot_available_at_utc"]))}
    )
    timeline = pd.merge_asof(
        timeline,
        events,
        left_on="available_at_utc",
        right_on="macro_available_at_utc",
        direction="backward",
    )
    timeline = pd.merge_asof(
        timeline.sort_values("available_at_utc"),
        positions,
        left_on="available_at_utc",
        right_on="cot_available_at_utc",
        direction="backward",
    )
    return timeline.sort_values("available_at_utc").reset_index(drop=True)


def _asof_join_market(market: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    if "timestamp_ms" not in market:
        raise MacroFuturesFoundationError("market frame lacks timestamp_ms")
    left = market.sort_values("timestamp_ms").copy()
    left["market_time_utc"] = pd.to_datetime(
        left["timestamp_ms"], unit="ms", utc=True
    ).astype("datetime64[ns, UTC]")
    right = daily.sort_values("available_at_utc").copy()
    right["available_at_utc"] = pd.to_datetime(right["available_at_utc"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    enriched = pd.merge_asof(
        left,
        right,
        left_on="market_time_utc",
        right_on="available_at_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    enriched["macro_available_at_ms"] = _timestamp_series_ms(enriched["macro_available_at_utc"])
    enriched["cot_available_at_ms"] = _timestamp_series_ms(enriched["cot_available_at_utc"])
    enriched["macro_staleness_days"] = (
        enriched["market_time_utc"] - enriched["macro_available_at_utc"]
    ).dt.total_seconds() / 86_400.0
    enriched["cot_staleness_days"] = (
        enriched["market_time_utc"] - enriched["cot_available_at_utc"]
    ).dt.total_seconds() / 86_400.0
    return enriched.drop(columns=["market_time_utc", "available_at_utc", "macro_available_at_utc", "cot_available_at_utc"])


def _timestamp_series_ms(values: pd.Series) -> pd.Series:
    result = pd.Series(pd.NA, index=values.index, dtype="Int64")
    mask = values.notna()
    normalized = pd.to_datetime(values.loc[mask], utc=True).astype("datetime64[ns, UTC]")
    result.loc[mask] = normalized.astype("int64") // 1_000_000
    return result


def _validate_daily_features(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> None:
    if frame.empty:
        raise MacroFuturesFoundationError("daily feature frame is empty")
    if frame["available_at_utc"].duplicated().any() or not frame["available_at_utc"].is_monotonic_increasing:
        raise MacroFuturesFoundationError("daily availability timestamps must be unique and sorted")
    if frame["available_at_utc"].min() > start + pd.Timedelta(days=14):
        raise MacroFuturesFoundationError("macro coverage starts too late")
    if frame["available_at_utc"].max() < end - pd.Timedelta(days=14):
        raise MacroFuturesFoundationError("macro coverage ends too early")


def _validate_enriched(frame: pd.DataFrame) -> None:
    if frame.empty or frame["timestamp_ms"].duplicated().any():
        raise MacroFuturesFoundationError("enriched market rows must be nonempty and unique")
    macro = frame["macro_available_at_ms"].dropna().astype("int64")
    cot = frame["cot_available_at_ms"].dropna().astype("int64")
    if (macro > frame.loc[macro.index, "timestamp_ms"]).any():
        raise MacroFuturesFoundationError("future macro value joined to market row")
    if (cot > frame.loc[cot.index, "timestamp_ms"]).any():
        raise MacroFuturesFoundationError("future CFTC value joined to market row")
    if frame["macro_available_at_ms"].notna().mean() < 0.95:
        raise MacroFuturesFoundationError("insufficient macro join coverage")
    if frame["cot_available_at_ms"].notna().mean() < 0.90:
        raise MacroFuturesFoundationError("insufficient CFTC join coverage")


def _artifact(path: Path, rows: int) -> dict[str, Any]:
    return {"path": str(path), "rows": rows, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _utc_iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat().replace("+00:00", "Z")
