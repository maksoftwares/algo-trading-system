from __future__ import annotations

import importlib.util
import json
import os
import re
from collections import OrderedDict
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, Mapping

import numpy as np
import pandas as pd

from step_3_common import HOUR_MS, sha256_bytes, sha256_file


class SourceDataError(RuntimeError):
    """Raised when frozen source bytes cannot be used safely."""


def load_bound_decoder(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("step3_bound_dukascopy_decoder", path)
    if spec is None or spec.loader is None:
        raise SourceDataError(f"Cannot import the bound decoder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LockedDukascopyStore:
    def __init__(
        self,
        *,
        root: Path,
        symbol: str,
        source_manifest: Mapping[str, Any],
        decoder: ModuleType,
        price_decimals: int,
        cache_size: int,
    ) -> None:
        self.root = root.resolve()
        self.symbol = symbol
        self.decoder = decoder
        self.price_decimals = int(price_decimals)
        self.cache_size = int(cache_size)
        self._hours: OrderedDict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = (
            OrderedDict()
        )
        self._month_rows: dict[str, dict[str, Any]] = {}
        self._verified_hours: dict[str, tuple[str, int, int]] = {}
        records = source_manifest["records"]
        self._frozen_records = {
            str(row["month"]): row for row in records if str(row["symbol"]) == symbol
        }
        if not self._frozen_records:
            raise SourceDataError(f"No frozen source records for {symbol}")
        source = source_manifest["by_symbol"][symbol]
        self.start_ms = int(
            pd.Timestamp(source["start_inclusive_utc"]).value // 1_000_000
        )
        self.end_ms = int(pd.Timestamp(source["end_exclusive_utc"]).value // 1_000_000)

    def _load_month(self, hour: pd.Timestamp) -> dict[str, Any]:
        month = hour.strftime("%Y-%m")
        if month in self._month_rows:
            return self._month_rows[month]
        record = self._frozen_records.get(month)
        if record is None:
            raise SourceDataError(f"{self.symbol} month outside frozen corpus: {month}")
        frozen = self.root / str(record["path"])
        if sha256_file(frozen) != str(record["manifest_sha256"]):
            raise SourceDataError(f"Frozen month manifest changed: {frozen}")
        frozen_payload = json.loads(frozen.read_text(encoding="utf-8"))
        acquisition = frozen.with_name("_ACQUISITION_MANIFEST.json")
        payload = json.loads(acquisition.read_text(encoding="utf-8"))
        rows = {str(row["path"]): row for row in payload["rows"]}
        if len(rows) != int(frozen_payload["expected_hour_files"]):
            raise SourceDataError(f"Acquisition row count changed: {acquisition}")
        file_set = [
            (Path(str(row["path"])).name, str(row["sha256"])) for row in payload["rows"]
        ]
        aggregate = (
            json.dumps(
                file_set,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")
        if sha256_bytes(aggregate) != str(frozen_payload["files_sha256"]):
            raise SourceDataError(f"Acquisition digest changed: {acquisition}")
        self._month_rows[month] = rows
        return rows

    def load_hour(self, hour_key: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        hour_key = int(hour_key)
        cached = self._hours.pop(hour_key, None)
        if cached is not None:
            self._hours[hour_key] = cached
            return cached
        hour_ms = hour_key * HOUR_MS
        if hour_ms < self.start_ms or hour_ms >= self.end_ms:
            empty_i = np.array([], dtype=np.int64)
            empty_f = np.array([], dtype=float)
            return empty_i, empty_f, empty_f.copy()
        hour = pd.Timestamp(hour_ms, unit="ms", tz="UTC")
        relative = (
            Path("raw")
            / self.symbol
            / f"year={hour.year:04d}"
            / f"month={hour.month:02d}"
            / f"{hour:%Y%m%d%H}.json"
        ).as_posix()
        row = self._load_month(hour).get(relative)
        if row is None:
            raise SourceDataError(f"Frozen hour is absent: {relative}")
        path = self.root / relative
        raw = path.read_bytes()
        if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != str(row["sha256"]):
            raise SourceDataError(f"Frozen raw hour changed: {path}")
        try:
            payload = json.loads(raw)
            arrays = self.decoder.decode_hour_payload(
                payload, hour, self.price_decimals
            )
        except Exception as exc:
            raise SourceDataError(f"Cannot decode frozen raw hour: {path}") from exc
        if len(arrays[0]) != int(row["tick_count"]):
            raise SourceDataError(f"Frozen raw tick count changed: {path}")
        result = tuple(np.asarray(array) for array in arrays)
        self._verified_hours[relative] = (
            str(row["sha256"]),
            int(row["bytes"]),
            int(row["tick_count"]),
        )
        self._hours[hour_key] = result  # type: ignore[assignment]
        while len(self._hours) > self.cache_size:
            self._hours.popitem(last=False)
        return result  # type: ignore[return-value]

    def hours_between(self, start_ms: int, end_ms: int) -> Iterator[int]:
        if end_ms < start_ms:
            return
        first = int(start_ms) // HOUR_MS
        final = int(end_ms) // HOUR_MS
        yield from range(first, final + 1)

    def ticks_between(
        self, start_ms: int, end_ms: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        chunks: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
        for hour_key in self.hours_between(start_ms, end_ms):
            values = self.load_hour(hour_key)
            if len(values[0]):
                chunks.append(values)
        if not chunks:
            empty_i = np.array([], dtype=np.int64)
            empty_f = np.array([], dtype=float)
            return empty_i, empty_f, empty_f.copy()
        times = np.concatenate([chunk[0] for chunk in chunks])
        bids = np.concatenate([chunk[1] for chunk in chunks])
        asks = np.concatenate([chunk[2] for chunk in chunks])
        left = int(np.searchsorted(times, start_ms, side="left"))
        right = int(np.searchsorted(times, end_ms, side="right"))
        return times[left:right], bids[left:right], asks[left:right]

    def first_quote_at_or_after(
        self, timestamp_ms: int, maximum_gap_ms: int
    ) -> tuple[int, float, float] | None:
        end_ms = int(timestamp_ms) + int(maximum_gap_ms)
        for hour_key in self.hours_between(timestamp_ms, end_ms):
            times, bids, asks = self.load_hour(hour_key)
            index = int(np.searchsorted(times, timestamp_ms, side="left"))
            if index < len(times) and int(times[index]) <= end_ms:
                return int(times[index]), float(bids[index]), float(asks[index])
        return None

    def audit(self) -> dict[str, Any]:
        records = sorted(self._verified_hours.items())
        digest = sha256_bytes(
            json.dumps(records, separators=(",", ":"), sort_keys=True).encode()
        )
        return {
            "symbol": self.symbol,
            "verified_hour_files": len(records),
            "verified_raw_bytes": int(sum(row[1][1] for row in records)),
            "verified_tick_rows": int(sum(row[1][2] for row in records)),
            "verified_record_set_sha256": digest,
            "all_opened_hours_sha256_verified": True,
        }


class ComexTradeStore:
    def __init__(self, *, manifest_path: Path, cache_size: int) -> None:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        pattern = re.compile(r"glbx-mdp3-(\d{8})\.trades\.dbn(?:\.zst)?$")
        self.records: dict[str, Mapping[str, Any]] = {}
        for row in payload["downloaded_files"]:
            match = pattern.search(str(row["path"]))
            if match:
                self.records[match.group(1)] = row
        if not self.records:
            raise SourceDataError("COMEX manifest contains no trades files")
        self.cache_size = int(cache_size)
        self._days: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self._verified: set[str] = set()

    def load_day(self, date_key: str) -> pd.DataFrame:
        cached = self._days.pop(date_key, None)
        if cached is not None:
            self._days[date_key] = cached
            return cached
        row = self.records.get(date_key)
        if row is None:
            return pd.DataFrame(
                columns=[
                    "ts_event",
                    "instrument_id",
                    "sequence",
                    "side",
                    "price",
                    "size",
                ]
            )
        path = Path(str(row["path"]))
        if path.stat().st_size != int(row["size_bytes"]) or sha256_file(path) != str(
            row["sha256"]
        ):
            raise SourceDataError(f"COMEX source changed: {path}")
        try:
            import databento as db

            frame = db.DBNStore.from_file(path).to_df(
                price_type="float", pretty_ts=True, map_symbols=False, schema="trades"
            )
        except Exception as exc:
            raise SourceDataError(f"Cannot decode COMEX source: {path}") from exc
        if not isinstance(frame, pd.DataFrame):
            frame = pd.concat(frame, ignore_index=False)
        if "ts_event" not in frame.columns and frame.index.name == "ts_event":
            frame = frame.reset_index()
        columns = ["ts_event", "instrument_id", "sequence", "side", "price", "size"]
        missing = sorted(set(columns) - set(frame.columns))
        if missing:
            raise SourceDataError(f"COMEX day lacks columns {missing}: {path}")
        result = frame[columns].copy()
        result["ts_event"] = pd.to_datetime(result["ts_event"], utc=True)
        result["side"] = result["side"].astype(str).str.upper().str[0]
        result = result.sort_values(
            ["ts_event", "instrument_id", "sequence"], kind="stable"
        ).reset_index(drop=True)
        self._verified.add(date_key)
        self._days[date_key] = result
        while len(self._days) > self.cache_size:
            self._days.popitem(last=False)
        return result

    def window(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        days = pd.date_range(start.normalize(), end.normalize(), freq="D")
        frames = [self.load_day(day.strftime("%Y%m%d")) for day in days]
        available = [frame for frame in frames if not frame.empty]
        if not available:
            return pd.DataFrame(
                columns=[
                    "ts_event",
                    "instrument_id",
                    "sequence",
                    "side",
                    "price",
                    "size",
                ]
            )
        result = pd.concat(available, ignore_index=True)
        return result.loc[
            result["ts_event"].gt(start) & result["ts_event"].le(end)
        ].reset_index(drop=True)

    def audit(self) -> dict[str, Any]:
        rows = [self.records[key] for key in sorted(self._verified)]
        return {
            "verified_daily_files": len(rows),
            "verified_compressed_bytes": int(
                sum(int(row["size_bytes"]) for row in rows)
            ),
            "all_opened_files_sha256_verified": True,
        }


def resolve_source_roots(config: Mapping[str, Any]) -> tuple[Path, Path]:
    source = config["source"]
    dukascopy = Path(
        os.environ.get(
            str(source["dukascopy_storage_environment_variable"]),
            str(source["dukascopy_default_storage_root"]),
        )
    ).resolve()
    comex = Path(
        os.environ.get(
            str(source["comex_storage_environment_variable"]),
            str(source["comex_default_storage_root"]),
        )
    ).resolve()
    return dukascopy, comex
