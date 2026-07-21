from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_STORAGE = Path("C:/SgeGoldDemandFoundationV1")
START_DATE = pd.Timestamp("2016-07-01")
END_EXCLUSIVE = pd.Timestamp("2026-07-01")
HISTORICAL_LAST_DATE = pd.Timestamp("2023-12-31")
HISTORICAL_LISTING_PAGES = 195
BASE_URL = "https://en.sge.com.cn"
HISTORICAL_INDEX_URL = BASE_URL + "/data_DailyReport?p={page}"
HISTORICAL_DETAIL_URL = BASE_URL + "/data_DailyReport/{article_id}"
MODERN_URL = (
    BASE_URL
    + "/h5_data_DailyReport?start_date={start}&end_date={end}&inst_ids=&p={page}"
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)
DETAIL_LINK_RE = re.compile(r'href="/data_DailyReport/(\d+)"')
TITLE_DATE_RE = re.compile(
    r"<h3>\s*Shanghai Gold Price\s*\(\s*([A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})",
    re.IGNORECASE,
)
PAGE_RE = re.compile(r"gotoPage\('/h5_data_DailyReport\?[^']*p=','(\d+)'\)")
KNOWN_NON_CONTRACT_REPORT_IDS = frozenset({"543406", "543424", "10000802"})
KNOWN_MALFORMED_REPORT_IDS = frozenset({"543277"})
KNOWN_TITLE_DATE_OVERRIDES = {"542439": "2017-04-18"}
KNOWN_TITLE_MONTH_ALIASES = {"Feburary": "February"}
POSITIONAL_CONTRACT_COLUMNS = [
    "Contract",
    "Open",
    "Highest",
    "Lowest",
    "Close",
    "Up/ Down (yuan)",
    "Up/ Down (%)",
    "Weighted Average Price",
    "Volume (Kg)",
    "Amount (yuan)",
    "Open Interest (Lot)",
    "Direction",
    "Delivery Volume (Lot)",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def fetch(url: str, path: Path, retries: int = 5) -> bytes:
    if path.is_file() and path.stat().st_size >= 500:
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": BASE_URL + "/data_DailyReport",
        },
    )
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=45) as response:
                payload = response.read()
            if len(payload) < 500:
                raise ValueError(f"Short SGE response ({len(payload)} bytes): {url}")
            temporary = path.with_suffix(path.suffix + ".part")
            temporary.write_bytes(payload)
            os.replace(temporary, path)
            time.sleep(0.15)
            return payload
        except (HTTPError, URLError, TimeoutError, ValueError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(8.0, 0.75 * (2**attempt)))
    raise AssertionError("unreachable")


def decode_html(payload: bytes) -> str:
    return payload.decode("utf-8", errors="replace")


def parse_detail_links(html: str) -> list[str]:
    return sorted(set(DETAIL_LINK_RE.findall(html)), key=int)


def _flatten_columns(columns: Iterable[object]) -> list[str]:
    result: list[str] = []
    for value in columns:
        if isinstance(value, tuple):
            text = " ".join(str(item) for item in value if str(item) != "nan")
        else:
            text = str(value)
        result.append(re.sub(r"\s+", " ", text).strip())
    return result


def _table_from_html(html: str) -> pd.DataFrame:
    tables = pd.read_html(io.StringIO(html))
    candidates = [table for table in tables if table.shape[1] >= 10]
    if len(candidates) != 1:
        raise ValueError(f"Expected one SGE contract table, found {len(candidates)}")
    table = candidates[0].copy()
    table.columns = _flatten_columns(table.columns)
    numeric_columns = all(str(column).isdigit() for column in table.columns)
    first_value = str(table.iloc[0, 0]).strip()
    if (
        numeric_columns
        and table.shape[1] == len(POSITIONAL_CONTRACT_COLUMNS)
        and re.match(r"^[A-Za-z]+(?:\d|\(|\.)", first_value)
    ):
        table.columns = POSITIONAL_CONTRACT_COLUMNS
        return table
    first_header = str(table.iloc[0, 0]).strip().lower()
    if first_header in {"contract", "variety"}:
        header_rows = 0
        for value in table.iloc[:, 0]:
            if str(value).strip().lower() != first_header:
                break
            header_rows += 1
        labels: list[str] = []
        for column in range(table.shape[1]):
            tokens: list[str] = []
            for value in table.iloc[:header_rows, column]:
                token = re.sub(r"\s+", " ", str(value)).strip()
                if token.lower() == "nan" or (tokens and token == tokens[-1]):
                    continue
                tokens.append(token)
            labels.append(" ".join(tokens))
        table.columns = labels
        table = table.iloc[header_rows:].reset_index(drop=True)
    return table


def parse_historical_detail(html: str, article_id: str) -> pd.DataFrame:
    if article_id in KNOWN_TITLE_DATE_OVERRIDES:
        if "Apri 18,2017" not in html:
            raise ValueError(f"Known SGE title typo changed for article {article_id}")
        trading_date = KNOWN_TITLE_DATE_OVERRIDES[article_id]
    else:
        match = TITLE_DATE_RE.search(html)
        if match is None:
            raise ValueError(
                f"Missing SGE trading date in title for article {article_id}"
            )
        month = KNOWN_TITLE_MONTH_ALIASES.get(match.group(1), match.group(1))
        date_text = f"{month} {match.group(2)}, {match.group(3)}"
        for date_format in ("%B %d, %Y", "%b %d, %Y"):
            try:
                trading_date = (
                    datetime.strptime(date_text, date_format).date().isoformat()
                )
                break
            except ValueError:
                continue
        else:
            raise ValueError(
                f"Unrecognized SGE trading date {date_text!r} for article {article_id}"
            )
    table = _table_from_html(html)
    table.insert(0, "Date", trading_date)
    table["source_article_id"] = str(article_id)
    table["source_type"] = "historical_detail"
    return table


def parse_modern_page(html: str) -> pd.DataFrame:
    table = _table_from_html(html)
    if "Date" not in table.columns:
        raise ValueError("Modern SGE table is missing Date")
    table["source_article_id"] = ""
    table["source_type"] = "modern_paginated"
    return table


def maximum_modern_page(html: str) -> int:
    pages = [int(value) for value in PAGE_RE.findall(html)]
    return max(pages, default=1)


def _normalized_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _canonical_columns(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "date": "date",
        "contract": "contract",
        "variety": "contract",
        "open": "open",
        "high": "high",
        "highest": "high",
        "low": "low",
        "lowest": "low",
        "close": "close",
        "up_down_yuan": "change_yuan",
        "up_down": "change_yuan",
        "up_down_": "change_yuan",
        "weighted_average_price": "weighted_average",
        "volume_kg": "volume_kg",
        "amount_yuan": "amount_yuan",
        "open_interest": "open_interest_lot",
        "open_interest_lot": "open_interest_lot",
        "direction": "direction",
        "delivery_volume": "delivery_volume_lot",
        "delivery_volume_lot": "delivery_volume_lot",
        "source_article_id": "source_article_id",
        "source_type": "source_type",
    }
    rename: dict[object, str] = {}
    percent_column: object | None = None
    normalized_columns = {_normalized_name(column) for column in frame.columns}
    for column in frame.columns:
        normalized = _normalized_name(column)
        if normalized in {"up_down_percent", "up_down_pct"} or (
            normalized.startswith("up_down") and "%" in str(column)
        ) or (
            normalized == "up_down" and "up_down_yuan" in normalized_columns
        ):
            percent_column = column
            continue
        if normalized in aliases:
            rename[column] = aliases[normalized]
    output = frame.rename(columns=rename).copy()
    if percent_column is not None:
        output = output.rename(columns={percent_column: "change_percent"})
    if not output.columns.is_unique:
        duplicate_columns = output.columns[output.columns.duplicated()].tolist()
        raise ValueError(
            f"SGE normalized table has duplicate columns: {duplicate_columns!r}"
        )
    required = {"date", "contract", "close", "volume_kg"}
    missing = sorted(required.difference(output.columns))
    if missing:
        raise ValueError(f"SGE normalized table missing columns: {missing}")
    for column in (
        "open",
        "high",
        "low",
        "close",
        "change_yuan",
        "change_percent",
        "weighted_average",
        "volume_kg",
        "amount_yuan",
        "open_interest_lot",
        "delivery_volume_lot",
    ):
        if column not in output:
            output[column] = np.nan
        output[column] = pd.to_numeric(
            output[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .replace({"-": np.nan, "--": np.nan, "nan": np.nan, "": np.nan}),
            errors="coerce",
        )
    output["date"] = pd.to_datetime(output["date"], errors="raise")
    output["contract"] = (
        output["contract"]
        .astype(str)
        .str.replace("（", "(", regex=False)
        .str.replace("）", ")", regex=False)
        .str.replace("Au9999", "Au99.99", regex=False)
        .str.replace("Au9995", "Au99.95", regex=False)
        .str.strip()
        .replace(
            {
                "Ag9999": "Ag99.99",
                "Au995": "Au99.5",
                "IAu100g": "iAu100g",
                "iAU100g": "iAu100g",
                "iAu995": "iAu99.5",
                "PGC30G": "PGC30g",
                "Pt9995": "Pt99.95",
            }
        )
    )
    valid_contract = output["contract"].str.fullmatch(
        r"[A-Za-z][A-Za-z0-9.]*(?:\([A-Za-z0-9+]+\))?"
    )
    output = output.loc[valid_contract].copy()
    if "direction" not in output:
        output["direction"] = ""
    direction_key = (
        output["direction"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.replace(r"[^a-z]", "", regex=True)
    )
    direction_map = {
        "": "",
        "longtoshort": "long_to_short",
        "shortolong": "short_to_long",
        "shorttolong": "short_to_long",
    }
    unknown_direction = sorted(set(direction_key).difference(direction_map))
    if unknown_direction:
        raise ValueError(f"Unknown SGE direction labels: {unknown_direction!r}")
    output["direction"] = direction_key.map(direction_map)
    output["source_article_id"] = output["source_article_id"].fillna("").astype(str)
    output["source_type"] = output["source_type"].fillna("").astype(str)
    columns = [
        "date",
        "contract",
        "open",
        "high",
        "low",
        "close",
        "change_yuan",
        "change_percent",
        "weighted_average",
        "volume_kg",
        "amount_yuan",
        "open_interest_lot",
        "direction",
        "delivery_volume_lot",
        "source_article_id",
        "source_type",
    ]
    return output[columns]


def _fetch_detail(
    article_id: str, raw_root: Path
) -> tuple[str, pd.DataFrame | None]:
    path = raw_root / "historical_details" / f"{article_id}.html"
    payload = fetch(HISTORICAL_DETAIL_URL.format(article_id=article_id), path)
    html = decode_html(payload)
    if article_id in KNOWN_NON_CONTRACT_REPORT_IDS:
        if "NYAuTN" not in html or "Reference" not in html:
            raise ValueError(f"Known non-contract SGE report changed: {article_id}")
        return article_id, None
    if article_id in KNOWN_MALFORMED_REPORT_IDS:
        malformed = _table_from_html(html)
        first_value = str(malformed.iloc[0, 0]).strip().lower()
        if malformed.shape[1] != 12 or first_value != "open":
            raise ValueError(f"Known malformed SGE report changed: {article_id}")
        return article_id, None
    return article_id, parse_historical_detail(html, article_id)


def collect_historical(raw_root: Path, workers: int) -> list[pd.DataFrame]:
    article_ids: set[str] = set()
    for page in range(1, HISTORICAL_LISTING_PAGES + 1):
        path = raw_root / "historical_index" / f"page_{page:03d}.html"
        html = decode_html(fetch(HISTORICAL_INDEX_URL.format(page=page), path))
        article_ids.update(parse_detail_links(html))
        if page % 25 == 0:
            print(f"historical index {page}/{HISTORICAL_LISTING_PAGES}", flush=True)
    if len(article_ids) < 1_500:
        raise ValueError(f"Too few historical SGE article IDs: {len(article_ids)}")
    frames: list[pd.DataFrame] = []
    ordered = sorted(article_ids, key=int)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_fetch_detail, article_id, raw_root): article_id
            for article_id in ordered
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            article_id, frame = future.result()
            if frame is None:
                print(f"excluded audited non-contract report {article_id}", flush=True)
                continue
            date = pd.Timestamp(frame["Date"].iloc[0])
            if START_DATE <= date <= HISTORICAL_LAST_DATE:
                frames.append(frame)
            if completed % 100 == 0:
                print(f"historical detail {completed}/{len(futures)}", flush=True)
    return frames


def _month_ranges() -> Iterable[tuple[pd.Timestamp, pd.Timestamp]]:
    for month in pd.period_range("2024-01", "2026-06", freq="M"):
        start = pd.Timestamp(month.start_time.date())
        end = min(pd.Timestamp(month.end_time.date()), END_EXCLUSIVE - pd.Timedelta(days=1))
        yield start, end


def collect_modern(raw_root: Path) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for start, end in _month_ranges():
        month = start.strftime("%Y-%m")
        first_path = raw_root / "modern" / month / "page_001.html"
        first_html = decode_html(
            fetch(
                MODERN_URL.format(
                    start=start.date(), end=end.date(), page=1
                ),
                first_path,
            )
        )
        pages = maximum_modern_page(first_html)
        frames.append(parse_modern_page(first_html))
        for page in range(2, pages + 1):
            path = raw_root / "modern" / month / f"page_{page:03d}.html"
            html = decode_html(
                fetch(
                    MODERN_URL.format(
                        start=start.date(), end=end.date(), page=page
                    ),
                    path,
                )
            )
            frames.append(parse_modern_page(html))
        print(f"modern {month}: {pages} pages", flush=True)
    return frames


def _raw_digest(raw_root: Path) -> tuple[int, str]:
    files = sorted(path for path in raw_root.rglob("*.html") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(raw_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return len(files), digest.hexdigest()


def write_outputs(storage: Path, frames: list[pd.DataFrame]) -> dict[str, object]:
    raw_table_rows = sum(len(frame) for frame in frames)
    normalized_frames: list[pd.DataFrame] = []
    for frame_index, frame in enumerate(frames):
        try:
            normalized_frames.append(_canonical_columns(frame))
        except ValueError as error:
            source_type = frame.get("source_type", pd.Series(dtype=str))
            article_id = frame.get("source_article_id", pd.Series(dtype=str))
            raise ValueError(
                "Failed to normalize SGE frame "
                f"{frame_index}: shape={frame.shape}, columns={list(frame.columns)!r}, "
                f"source_type={source_type.head(1).tolist()!r}, "
                f"source_article_id={article_id.head(1).tolist()!r}"
            ) from error
    combined = pd.concat(normalized_frames, ignore_index=True)
    combined = combined.loc[
        combined["date"].ge(START_DATE) & combined["date"].lt(END_EXCLUSIVE)
    ].copy()
    combined = combined.sort_values(["date", "contract"], kind="mergesort")
    duplicate = combined.duplicated(["date", "contract"], keep=False)
    if duplicate.any():
        duplicate_rows = combined.loc[duplicate]
        value_columns = [
            column
            for column in combined.columns
            if column not in {"source_article_id", "source_type"}
        ]
        conflict_keys: list[tuple[pd.Timestamp, str]] = []
        for key, group in duplicate_rows.groupby(["date", "contract"], sort=True):
            if len(group[value_columns].drop_duplicates()) > 1:
                conflict_keys.append(key)
        if conflict_keys:
            sample_keys = set(conflict_keys[:5])
            sample = duplicate_rows.loc[
                duplicate_rows.apply(
                    lambda row: (row["date"], row["contract"]) in sample_keys,
                    axis=1,
                )
            ]
            raise ValueError(
                "Conflicting duplicate SGE contract rows: "
                + sample.to_json(orient="records", date_format="iso")
            )
        combined = combined.drop_duplicates(["date", "contract"], keep="first")
    combined = combined.reset_index(drop=True)
    if combined.empty or combined["date"].min() > START_DATE + pd.Timedelta(days=7):
        raise ValueError("SGE source does not cover the registered start")
    normalized = storage / "normalized" / "sge_daily_contracts_v1.parquet"
    normalized.parent.mkdir(parents=True, exist_ok=True)
    temporary = normalized.with_suffix(".parquet.part")
    combined.to_parquet(temporary, index=False)
    os.replace(temporary, normalized)
    raw_count, raw_digest = _raw_digest(storage / "raw")
    per_contract = combined.groupby("contract", sort=True).size().astype(int).to_dict()
    manifest: dict[str, object] = {
        "schema_version": "sge_daily_contracts_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "source": "Shanghai Gold Exchange public daily reports",
        "historical_index_url": HISTORICAL_INDEX_URL,
        "historical_detail_url": HISTORICAL_DETAIL_URL,
        "modern_url": MODERN_URL,
        "start_date": combined["date"].min().date().isoformat(),
        "end_date": combined["date"].max().date().isoformat(),
        "rows": int(len(combined)),
        "raw_table_rows_before_contract_filter": int(raw_table_rows),
        "non_contract_rows_filtered": int(
            raw_table_rows - sum(len(frame) for frame in normalized_frames)
        ),
        "unique_dates": int(combined["date"].nunique()),
        "duplicate_date_contract_rows": int(
            combined.duplicated(["date", "contract"]).sum()
        ),
        "per_contract_rows": per_contract,
        "normalized_path": str(normalized),
        "normalized_sha256": sha256_file(normalized),
        "raw_html_file_count": raw_count,
        "raw_digest": raw_digest,
        "excluded_non_contract_report_ids": sorted(KNOWN_NON_CONTRACT_REPORT_IDS),
        "excluded_malformed_report_ids": sorted(KNOWN_MALFORMED_REPORT_IDS),
        "title_date_overrides": KNOWN_TITLE_DATE_OVERRIDES,
        "title_month_aliases": KNOWN_TITLE_MONTH_ALIASES,
        "xau_outcomes_inspected": False,
        "paid_data_used": False,
        "databento_used": False,
        "raw_data_committed": False,
    }
    manifest["manifest_sha256"] = canonical_hash(manifest)
    manifest_path = storage / "normalized" / "sge_daily_contracts_v1.manifest.json"
    temporary_manifest = manifest_path.with_suffix(".json.part")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary_manifest, manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage",
        type=Path,
        default=Path(os.environ.get("SGE_DAILY_DATA_ROOT", DEFAULT_STORAGE)),
    )
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    storage = args.storage.resolve()
    raw_root = storage / "raw"
    frames = collect_historical(raw_root, args.workers)
    frames.extend(collect_modern(raw_root))
    manifest = write_outputs(storage, frames)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
