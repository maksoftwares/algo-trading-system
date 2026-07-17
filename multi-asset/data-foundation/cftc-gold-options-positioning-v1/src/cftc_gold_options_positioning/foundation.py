from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


COMBINED_DATASET = "kh3c-gbw2"
FUTURES_ONLY_DATASET = "72hh-3qpy"
CONTRACT_CODE = "088691"
API_ROOT = "https://publicreporting.cftc.gov/resource"
DEFAULT_STORAGE_ROOT = Path("C:/CftcGoldOptionsPositioningV1")
STORAGE_ENV = "CFTC_GOLD_OPTIONS_DATA_ROOT"

IDENTITY_COLUMNS = (
    "id",
    "market_and_exchange_names",
    "report_date_as_yyyy_mm_dd",
    "cftc_contract_market_code",
    "open_interest_all",
)
POSITION_COLUMNS = {
    "producer": ("prod_merc_positions_long", "prod_merc_positions_short", None),
    "swap": (
        "swap_positions_long_all",
        "swap__positions_short_all",
        "swap__positions_spread_all",
    ),
    "managed_money": (
        "m_money_positions_long_all",
        "m_money_positions_short_all",
        "m_money_positions_spread",
    ),
    "other_reportable": (
        "other_rept_positions_long",
        "other_rept_positions_short",
        "other_rept_positions_spread",
    ),
    "nonreportable": (
        "nonrept_positions_long_all",
        "nonrept_positions_short_all",
        None,
    ),
}
SOURCE_COLUMNS = tuple(
    dict.fromkeys(
        [
            *IDENTITY_COLUMNS,
            *[
                column
                for columns in POSITION_COLUMNS.values()
                for column in columns
                if column is not None
            ],
        ]
    )
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(value)
    os.replace(temporary, path)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    _atomic_bytes(path, payload.encode("utf-8"))


def _dataset_url(dataset: str) -> str:
    parameters = {
        "$select": ",".join(SOURCE_COLUMNS),
        "$where": (
            f"cftc_contract_market_code='{CONTRACT_CODE}' AND "
            "report_date_as_yyyy_mm_dd >= '2009-09-01T00:00:00.000'"
        ),
        "$order": "report_date_as_yyyy_mm_dd ASC",
        "$limit": "50000",
    }
    return f"{API_ROOT}/{dataset}.csv?{urlencode(parameters)}"


def _download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "algo-trading-system-research/1.0"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.startswith((b"id,", b'"id",')):
        raise ValueError("CFTC response was not the expected CSV schema")
    return payload


def _normalize_source(frame: pd.DataFrame, expected_type: str) -> pd.DataFrame:
    missing = set(SOURCE_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"CFTC source is missing columns: {sorted(missing)}")
    result = frame[list(SOURCE_COLUMNS)].copy()
    result["report_date"] = pd.to_datetime(
        result.pop("report_date_as_yyyy_mm_dd"), utc=True, errors="raise"
    ).dt.normalize()
    if result["report_date"].duplicated().any():
        raise ValueError(f"Duplicate {expected_type} CFTC report dates")
    if not result["cftc_contract_market_code"].astype(str).eq(CONTRACT_CODE).all():
        raise ValueError("Unexpected CFTC contract code")
    numeric = ["open_interest_all"] + [
        column
        for columns in POSITION_COLUMNS.values()
        for column in columns
        if column is not None
    ]
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
    result["source_type"] = expected_type
    return result.sort_values("report_date", kind="mergesort").reset_index(drop=True)


def build_curated_frame(combined: pd.DataFrame, futures_only: pd.DataFrame) -> pd.DataFrame:
    combined = _normalize_source(combined, "combined")
    futures_only = _normalize_source(futures_only, "futures_only")
    if set(combined["report_date"]) != set(futures_only["report_date"]):
        only_combined = set(combined["report_date"]).difference(futures_only["report_date"])
        only_futures = set(futures_only["report_date"]).difference(combined["report_date"])
        raise ValueError(
            "Unpaired CFTC report dates: "
            f"combined_only={len(only_combined)}, futures_only={len(only_futures)}"
        )
    left = combined.drop(columns=["source_type"]).add_suffix("_combined")
    right = futures_only.drop(columns=["source_type"]).add_suffix("_futures")
    result = left.merge(
        right,
        left_on="report_date_combined",
        right_on="report_date_futures",
        how="inner",
        validate="one_to_one",
    )
    result["report_date"] = result.pop("report_date_combined")
    result = result.drop(columns=["report_date_futures"])
    days_to_monday = (7 - result["report_date"].dt.dayofweek) % 7
    days_to_monday = days_to_monday.mask(days_to_monday.eq(0), 7)
    result["available_utc"] = result["report_date"] + pd.to_timedelta(
        days_to_monday, unit="D"
    )
    result["options_open_interest_delta_equivalent"] = (
        result["open_interest_all_combined"] - result["open_interest_all_futures"]
    )
    if result["options_open_interest_delta_equivalent"].le(0.0).any():
        raise ValueError("Nonpositive option-equivalent open interest")
    for category, columns in POSITION_COLUMNS.items():
        long_column, short_column, spread_column = columns
        result[f"{category}_combined_net"] = (
            result[f"{long_column}_combined"] - result[f"{short_column}_combined"]
        )
        result[f"{category}_futures_net"] = (
            result[f"{long_column}_futures"] - result[f"{short_column}_futures"]
        )
        for side, source_column in (("long", long_column), ("short", short_column)):
            result[f"{category}_options_{side}"] = (
                result[f"{source_column}_combined"]
                - result[f"{source_column}_futures"]
            )
        result[f"{category}_options_net"] = (
            result[f"{category}_options_long"] - result[f"{category}_options_short"]
        )
        if spread_column is not None:
            result[f"{category}_options_spread"] = (
                result[f"{spread_column}_combined"]
                - result[f"{spread_column}_futures"]
            )
    keep = [
        "report_date",
        "available_utc",
        "market_and_exchange_names_combined",
        "cftc_contract_market_code_combined",
        "open_interest_all_combined",
        "open_interest_all_futures",
        "options_open_interest_delta_equivalent",
        *[
            column
            for category, columns in POSITION_COLUMNS.items()
            for column in (
                f"{category}_combined_net",
                f"{category}_futures_net",
                f"{category}_options_long",
                f"{category}_options_short",
                f"{category}_options_net",
                *(
                    (f"{category}_options_spread",)
                    if columns[2] is not None
                    else ()
                ),
            )
        ],
    ]
    result = result[keep].sort_values("report_date", kind="mergesort")
    if not result["available_utc"].dt.dayofweek.eq(0).all():
        raise ValueError("CFTC availability must be Monday")
    return result.reset_index(drop=True)


def load_curated(storage_root: Path | None = None) -> pd.DataFrame:
    root = storage_root or Path(os.environ.get(STORAGE_ENV, DEFAULT_STORAGE_ROOT))
    return pd.read_parquet(root / "curated" / "gold_options_positioning.parquet")


def acquire() -> int:
    root = Path(os.environ.get(STORAGE_ENV, DEFAULT_STORAGE_ROOT)).resolve()
    raw_root = root / "raw"
    curated_root = root / "curated"
    combined_url = _dataset_url(COMBINED_DATASET)
    futures_url = _dataset_url(FUTURES_ONLY_DATASET)
    combined_bytes = _download(combined_url)
    futures_bytes = _download(futures_url)
    combined_path = raw_root / "cftc_gold_combined.csv"
    futures_path = raw_root / "cftc_gold_futures_only.csv"
    _atomic_bytes(combined_path, combined_bytes)
    _atomic_bytes(futures_path, futures_bytes)
    combined = pd.read_csv(io.BytesIO(combined_bytes), dtype=str)
    futures_only = pd.read_csv(io.BytesIO(futures_bytes), dtype=str)
    curated = build_curated_frame(combined, futures_only)
    curated_root.mkdir(parents=True, exist_ok=True)
    curated_path = curated_root / "gold_options_positioning.parquet"
    temporary = curated_path.with_suffix(".parquet.part")
    curated.to_parquet(temporary, index=False)
    os.replace(temporary, curated_path)
    manifest = {
        "schema_version": "cftc_gold_options_positioning_foundation_v1",
        "acquired_utc": datetime.now(UTC).isoformat(),
        "official_source": "U.S. Commodity Futures Trading Commission",
        "contract_market_code": CONTRACT_CODE,
        "combined_dataset_id": COMBINED_DATASET,
        "futures_only_dataset_id": FUTURES_ONLY_DATASET,
        "combined_url": combined_url,
        "futures_only_url": futures_url,
        "rows": int(len(curated)),
        "first_report_date": curated["report_date"].min().isoformat(),
        "last_report_date": curated["report_date"].max().isoformat(),
        "availability_rule": "first_Monday_strictly_after_report_date_00_00_UTC",
        "files": {
            "raw/cftc_gold_combined.csv": _sha256(combined_path),
            "raw/cftc_gold_futures_only.csv": _sha256(futures_path),
            "curated/gold_options_positioning.parquet": _sha256(curated_path),
        },
        "api_key_used": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "strategy_scoring_performed": False,
    }
    _atomic_json(root / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0
