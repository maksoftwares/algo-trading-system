from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_dukas_crossvenue_foundation_v22_1.json"
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


def path_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        shown = resolved.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        shown = str(resolved)
    return {
        "path": shown,
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(REPO.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def window(config: dict[str, Any]) -> tuple[pd.Timestamp, pd.Timestamp]:
    return (
        pd.Timestamp(config["window"]["start_inclusive_utc"]),
        pd.Timestamp(config["window"]["end_exclusive_utc"]),
    )


def expected_capital_paths(config: dict[str, Any]) -> list[Path]:
    start, end = window(config)
    directory = Path(config["capital"]["directory"])
    prefix = str(config["capital"]["filename_prefix"])
    dates = pd.date_range(start.normalize(), end - pd.Timedelta(days=1), freq="D")
    return [directory / f"{prefix}{date:%Y%m%d}.csv" for date in dates]


def expected_dukascopy_paths(config: dict[str, Any]) -> list[Path]:
    start, end = window(config)
    directory = Path(config["dukascopy"]["directory"])
    hours = pd.date_range(start.floor("h"), end - pd.Timedelta(hours=1), freq="h")
    return [
        directory
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json"
        for hour in hours
    ]


def build_source_manifest(config: dict[str, Any]) -> dict[str, Any]:
    expected_capital = expected_capital_paths(config)
    dukascopy = expected_dukascopy_paths(config)
    missing_capital = [path for path in expected_capital if not path.is_file()]
    missing_dates = [path.stem.rsplit("_", 1)[-1] for path in missing_capital]
    missing_dates = [f"{value[:4]}-{value[4:6]}-{value[6:8]}" for value in missing_dates]
    allowed_missing = list(config["capital"]["allowed_missing_dates"])
    if missing_dates != allowed_missing:
        raise FileNotFoundError(
            f"Unexpected V22.1 Capital missing dates: {missing_dates}"
        )
    capital = [path for path in expected_capital if path.is_file()]
    missing_dukascopy = [str(path) for path in dukascopy if not path.is_file()]
    if missing_dukascopy:
        raise FileNotFoundError(
            f"V22.1 Dukascopy source files missing: {missing_dukascopy[:10]}"
        )
    payload: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "window": config["window"],
        "capital_files": [path_record(path) for path in capital],
        "dukascopy_files": [path_record(path) for path in dukascopy],
        "capital_file_count": len(capital),
        "dukascopy_file_count": len(dukascopy),
        "missing_capital_dates": missing_dates,
    }
    payload["manifest_sha256"] = canonical_hash(payload, "manifest_sha256")
    return payload


def verify_source_files(manifest: dict[str, Any]) -> None:
    if canonical_hash(manifest, "manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("V22.1 source manifest self-hash mismatch")
    for section in ("capital_files", "dukascopy_files"):
        for record in manifest[section]:
            path = Path(record["path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            if path.stat().st_size != int(record["bytes"]):
                raise ValueError(f"V22.1 source size changed: {path}")
            if sha256_file(path) != record["sha256"]:
                raise ValueError(f"V22.1 source hash changed: {path}")


class DukascopyRawStore:
    def __init__(self, directory: Path, price_decimals: int) -> None:
        self.directory = directory.resolve()
        self.factor = float(10**price_decimals)

    @lru_cache(maxsize=48)
    def load_hour(self, hour_key: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        hour = pd.Timestamp(hour_key * 3_600_000, unit="ms", tz="UTC")
        path = (
            self.directory
            / f"year={hour.year:04d}"
            / f"month={hour.month:02d}"
            / f"{hour:%Y%m%d%H}.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = (
            "timestamp",
            "multiplier",
            "bid",
            "ask",
            "times",
            "bids",
            "asks",
            "bidVolumes",
            "askVolumes",
        )
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"Dukascopy fields missing in {path}: {missing}")
        arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
        lengths = [len(payload[key]) for key in arrays]
        if len(set(lengths)) != 1:
            raise ValueError(f"Dukascopy arrays differ in {path}: {lengths}")
        if lengths[0] == 0:
            empty_i = np.array([], dtype=np.int64)
            empty_f = np.array([], dtype=float)
            return empty_i, empty_f, empty_f.copy()
        multiplier = float(payload["multiplier"])
        if not np.isfinite(multiplier) or multiplier <= 0.0:
            raise ValueError(f"Dukascopy multiplier is invalid: {path}")
        times = int(payload["timestamp"]) + np.cumsum(
            np.asarray(payload["times"], dtype=np.int64), dtype=np.int64
        )
        bids = np.floor(
            (
                float(payload["bid"])
                + np.cumsum(np.asarray(payload["bids"], dtype=float)) * multiplier
            )
            * self.factor
            + 0.5
            + 1e-9
        ) / self.factor
        asks = np.floor(
            (
                float(payload["ask"])
                + np.cumsum(np.asarray(payload["asks"], dtype=float)) * multiplier
            )
            * self.factor
            + 0.5
            + 1e-9
        ) / self.factor
        if np.any(np.diff(times) < 0):
            raise ValueError(f"Dukascopy timestamps are unsorted: {path}")
        hour_start_ms = int(hour.value // 1_000_000)
        if times[0] < hour_start_ms or times[-1] >= hour_start_ms + 3_600_000:
            raise ValueError(f"Dukascopy ticks escape their source hour: {path}")
        if np.any(~np.isfinite(bids)) or np.any(~np.isfinite(asks)):
            raise ValueError(f"Dukascopy quote is non-finite: {path}")
        if np.any(bids <= 0.0) or np.any(asks < bids):
            raise ValueError(f"Dukascopy quote is invalid: {path}")
        return times, bids, asks

    def match_backward(
        self, timestamps_ms: np.ndarray, maximum_age_ms: int
    ) -> pd.DataFrame:
        timestamps = np.asarray(timestamps_ms, dtype=np.int64)
        matched_time = np.full(len(timestamps), -1, dtype=np.int64)
        matched_bid = np.full(len(timestamps), np.nan, dtype=float)
        matched_ask = np.full(len(timestamps), np.nan, dtype=float)
        hour_keys = timestamps // 3_600_000
        for hour_key in np.unique(hour_keys):
            positions = np.flatnonzero(hour_keys == hour_key)
            query = timestamps[positions]
            times, bids, asks = self.load_hour(int(hour_key))
            if len(times) == 0:
                continue
            indices = np.searchsorted(times, query, side="right") - 1
            valid = indices >= 0
            valid_positions = positions[valid]
            valid_indices = indices[valid]
            matched_time[valid_positions] = times[valid_indices]
            matched_bid[valid_positions] = bids[valid_indices]
            matched_ask[valid_positions] = asks[valid_indices]
        age = timestamps - matched_time
        valid_age = (matched_time >= 0) & (age >= 0) & (age <= maximum_age_ms)
        return pd.DataFrame(
            {
                "dukas_timestamp_ms": np.where(valid_age, matched_time, -1),
                "dukas_bid": np.where(valid_age, matched_bid, np.nan),
                "dukas_ask": np.where(valid_age, matched_ask, np.nan),
                "dukas_quote_age_ms": np.where(valid_age, age, np.nan),
                "pair_valid": valid_age,
            }
        )


def _fresh_mask(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.lower().isin(("true", "1"))


def load_capital_quotes(
    manifest: dict[str, Any], config: dict[str, Any]
) -> pd.DataFrame:
    columns = [
        "tick_time_msc",
        "seconds_since_tick",
        "tick_fresh",
        "account",
        "server",
        "symbol",
        "bid",
        "ask",
    ]
    frames: list[pd.DataFrame] = []
    for record in manifest["capital_files"]:
        frame = pd.read_csv(record["path"], usecols=columns)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        raise ValueError("No Capital quote rows were found")
    quotes = pd.concat(frames, ignore_index=True)
    capital = config["capital"]
    identity = (
        quotes["account"].eq(int(capital["account"]))
        & quotes["server"].eq(str(capital["server"]))
        & quotes["symbol"].eq(str(capital["symbol"]))
    )
    if not identity.all():
        raise ValueError("Capital source identity changed")
    quotes["tick_time_msc"] = pd.to_numeric(
        quotes["tick_time_msc"], errors="coerce"
    )
    quotes["seconds_since_tick"] = pd.to_numeric(
        quotes["seconds_since_tick"], errors="coerce"
    )
    quotes["bid"] = pd.to_numeric(quotes["bid"], errors="coerce")
    quotes["ask"] = pd.to_numeric(quotes["ask"], errors="coerce")
    start, end = window(config)
    start_ms = int(start.value // 1_000_000)
    end_ms = int(end.value // 1_000_000)
    valid = (
        quotes["tick_time_msc"].ge(start_ms)
        & quotes["tick_time_msc"].lt(end_ms)
        & quotes["seconds_since_tick"].le(
            int(capital["maximum_seconds_since_tick"])
        )
        & quotes["bid"].gt(0.0)
        & quotes["ask"].ge(quotes["bid"])
    )
    if capital["require_tick_fresh"]:
        valid &= _fresh_mask(quotes["tick_fresh"])
    quotes = quotes.loc[valid].copy()
    quotes["capital_timestamp_ms"] = quotes["tick_time_msc"].astype(np.int64)
    quotes = quotes.sort_values("capital_timestamp_ms", kind="mergesort")
    quotes = quotes.drop_duplicates("capital_timestamp_ms", keep="last")
    quotes = quotes.rename(columns={"bid": "capital_bid", "ask": "capital_ask"})
    return quotes[
        [
            "capital_timestamp_ms",
            "capital_bid",
            "capital_ask",
            "seconds_since_tick",
        ]
    ].reset_index(drop=True)


def build_paired_quotes(
    capital: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    dukascopy = config["dukascopy"]
    store = DukascopyRawStore(
        Path(dukascopy["directory"]), int(dukascopy["price_decimals"])
    )
    matches = store.match_backward(
        capital["capital_timestamp_ms"].to_numpy(dtype=np.int64),
        int(dukascopy["maximum_backward_quote_age_ms"]),
    )
    merged = pd.concat([capital.reset_index(drop=True), matches], axis=1)
    paired = merged.loc[merged["pair_valid"]].drop(columns="pair_valid").copy()
    paired["timestamp_utc"] = pd.to_datetime(
        paired["capital_timestamp_ms"], unit="ms", utc=True
    )
    paired["dukas_timestamp_utc"] = pd.to_datetime(
        paired["dukas_timestamp_ms"], unit="ms", utc=True
    )
    paired["capital_mid"] = (paired["capital_bid"] + paired["capital_ask"]) / 2.0
    paired["dukas_mid"] = (paired["dukas_bid"] + paired["dukas_ask"]) / 2.0
    paired["capital_spread"] = paired["capital_ask"] - paired["capital_bid"]
    paired["dukas_spread"] = paired["dukas_ask"] - paired["dukas_bid"]
    paired["capital_minus_dukas_mid"] = paired["capital_mid"] - paired["dukas_mid"]
    paired["date_utc"] = paired["timestamp_utc"].dt.strftime("%Y-%m-%d")
    columns = [
        "timestamp_utc",
        "capital_timestamp_ms",
        "capital_bid",
        "capital_ask",
        "capital_mid",
        "capital_spread",
        "dukas_timestamp_utc",
        "dukas_timestamp_ms",
        "dukas_bid",
        "dukas_ask",
        "dukas_mid",
        "dukas_spread",
        "dukas_quote_age_ms",
        "capital_minus_dukas_mid",
        "date_utc",
    ]
    paired = paired.loc[:, columns].sort_values(
        "timestamp_utc", kind="mergesort"
    ).reset_index(drop=True)
    audit = {
        "capital_fresh_unique_quotes": int(len(capital)),
        "paired_quotes": int(len(paired)),
        "pair_coverage": float(len(paired) / len(capital)) if len(capital) else 0.0,
        "pairing_is_backward_only": bool(
            paired["dukas_timestamp_ms"].le(paired["capital_timestamp_ms"]).all()
        ),
        "maximum_observed_dukas_age_ms": float(
            paired["dukas_quote_age_ms"].max()
        ),
        "first_pair_utc": paired["timestamp_utc"].min().isoformat(),
        "last_pair_utc": paired["timestamp_utc"].max().isoformat(),
        "future_columns_present": False,
        "labels_present": False,
    }
    return paired, audit


def build_daily_audit(paired: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for date, group in paired.groupby("date_utc", sort=True):
        basis = group["capital_minus_dukas_mid"].astype(float)
        records.append(
            {
                "date_utc": date,
                "paired_quotes": int(len(group)),
                "capital_spread_median": float(group["capital_spread"].median()),
                "dukas_spread_median": float(group["dukas_spread"].median()),
                "dukas_quote_age_ms_median": float(
                    group["dukas_quote_age_ms"].median()
                ),
                "basis_mid_median": float(basis.median()),
                "basis_mid_q05": float(basis.quantile(0.05)),
                "basis_mid_q95": float(basis.quantile(0.95)),
                "basis_mid_std": float(basis.std(ddof=1)),
            }
        )
    return pd.DataFrame(records)


def render_markdown(audit: dict[str, Any], daily: pd.DataFrame) -> str:
    active_days = int(daily["paired_quotes"].gt(0).sum())
    return (
        "# Capital-Dukascopy Cross-Venue Foundation V22.1\n\n"
        f"Paired quotes: **{audit['paired_quotes']:,}** from "
        f"{audit['capital_fresh_unique_quotes']:,} fresh unique Capital quotes "
        f"({audit['pair_coverage']:.2%} coverage).\n\n"
        f"Active UTC dates: **{active_days}**. Maximum backward Dukascopy quote "
        f"age: **{audit['maximum_observed_dukas_age_ms']:.0f} ms**.\n\n"
        "Every match is backward-only. This dataset contains no future values, "
        "labels, directions, signals, P&L, or execution authorization.\n"
    )


def verify_contract(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(payload, "contract_sha256") != payload["contract_sha256"]:
        raise ValueError("V22.1 contract self-hash mismatch")
    for record in payload["package_files"]:
        package_path = REPO / record["path"]
        if sha256_file(package_path) != record["sha256"]:
            raise ValueError(f"Locked V22.1 file changed: {record['path']}")
    manifest_path = root / config["outputs"]["directory"] / config["outputs"][
        "source_manifest"
    ]
    if sha256_file(manifest_path) != payload["source_manifest_file_sha256"]:
        raise ValueError("Locked V22.1 source manifest changed")
    return payload
