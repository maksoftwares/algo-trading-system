from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/eurusd-neutral-dtcc-fx-options-v1"
)
ENDPOINT = "https://pddata.dtcc.com/ppd/api/search/webdisplay"
REFERER = "https://pddata.dtcc.com/ppd/search"
UPI_SHORT_NAMES = {
    "CALL": "NA/O Van Call EUR USD",
    "PUT": "NA/O Van Put EUR USD",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def query_payload(date: pd.Timestamp, option_kind: str) -> dict[str, Any]:
    day = date.strftime("%Y-%m-%d")
    return {
        "jurisdiction": "CFTC",
        "assetClass": "FOREIGNEXCHANGE",
        "currency": "",
        "minNotionalAmount": "0",
        "maxNotionalAmount": "9999999999999999999999999999",
        "displayType": "w",
        "disseminationDateTimeLow": f"{day}T00:00:00.000Z",
        "disseminationDateTimeHigh": f"{day}T23:59:00.000Z",
        "productId": None,
        "underlyingAsset": None,
        "upi": None,
        "upiShortName": UPI_SHORT_NAMES[option_kind],
        "name": None,
        "searchIndicator": "post",
    }


def validate_response(payload: dict[str, Any], path: Path) -> None:
    if payload.get("errorList"):
        raise RuntimeError(
            f"DTCC query errors for {path.name}: {payload['errorList']!r}"
        )
    if not isinstance(payload.get("tradeList"), list):
        raise RuntimeError(f"Unexpected DTCC schema for {path.name}")


def fetch_one(
    date: pd.Timestamp,
    option_kind: str,
    raw_root: Path,
    *,
    force: bool,
    maximum_attempts: int,
) -> dict[str, Any]:
    path = raw_root / f"{date:%Y%m%d}_{option_kind}.json"
    if path.exists() and not force:
        cached = json.loads(path.read_text(encoding="utf-8"))
        validate_response(cached, path)
        return {
            "path": path,
            "cached": True,
            "rows": len(cached["tradeList"]),
        }

    body = json.dumps(
        query_payload(date, option_kind),
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": REFERER,
            "User-Agent": "eurusd-causal-research/1.0",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, maximum_attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            validate_response(parsed, path)
            canonical = json.dumps(
                parsed,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            temporary = path.with_suffix(".tmp")
            temporary.write_text(canonical, encoding="utf-8")
            temporary.replace(path)
            return {
                "path": path,
                "cached": False,
                "rows": len(parsed["tradeList"]),
            }
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            RuntimeError,
        ) as exc:
            last_error = exc
            if attempt < maximum_attempts:
                time.sleep(min(2**attempt, 20))
    raise RuntimeError(
        f"DTCC acquisition failed for {date.date()} {option_kind}"
    ) from last_error


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def qualified_trade(
    row: dict[str, Any],
    option_kind: str,
    report_date: pd.Timestamp,
) -> dict[str, Any] | None:
    if row.get("actionType") != "NEWT":
        return None
    if row.get("eventType") != "TRAD":
        return None
    if str(row.get("packageIndicator", "")).upper() != "FALSE":
        return None
    if row.get("uniqueProductIdentifierUnderlierName") != "EUR USD":
        return None
    expected_encoded = UPI_SHORT_NAMES[option_kind].replace("/", "%2F").replace(
        " ", "%20"
    )
    if row.get("uniqueProductIdentifierShortName") != expected_encoded:
        return None

    dissemination = pd.to_datetime(
        row.get("disseminationTimestamp"), utc=True, errors="coerce"
    )
    execution = pd.to_datetime(
        row.get("executionTimestamp"), utc=True, errors="coerce"
    )
    expiration = pd.to_datetime(
        row.get("expirationDate"), utc=True, errors="coerce"
    )
    if pd.isna(dissemination) or pd.isna(execution) or pd.isna(expiration):
        return None
    if dissemination.date() != report_date.date():
        return None
    delay_seconds = (dissemination - execution).total_seconds()
    if delay_seconds < 0 or delay_seconds > 24 * 3600:
        return None
    tenor_days = (expiration.normalize() - execution.normalize()).days
    if tenor_days < 7 or tenor_days > 90:
        return None

    if option_kind == "CALL":
        if row.get("callCurrencyLeg1") != "EUR":
            return None
        eur_notional = parse_number(row.get("callAmountLeg1"))
    else:
        if row.get("putCurrencyLeg1") != "EUR":
            return None
        eur_notional = parse_number(row.get("putAmountLeg1"))
    if row.get("optionPremiumCurrency") != "USD":
        return None
    usd_premium = parse_number(row.get("optionPremiumAmount"))
    if (
        eur_notional is None
        or usd_premium is None
        or eur_notional <= 0
        or usd_premium <= 0
    ):
        return None

    identifier = str(row.get("disseminationIdentifier", "")).strip()
    if not identifier:
        return None
    return {
        "dissemination_identifier": identifier,
        "execution_timestamp": execution,
        "dissemination_timestamp": dissemination,
        "expiration_date": expiration,
        "tenor_days": tenor_days,
        "eur_notional": eur_notional,
        "usd_premium": usd_premium,
    }


def parse_daily(
    path: Path,
    option_kind: str,
    report_date: pd.Timestamp,
) -> dict[str, Any]:
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    validate_response(payload, path)
    qualified: dict[str, dict[str, Any]] = {}
    for row in payload["tradeList"]:
        parsed = qualified_trade(row, option_kind, report_date)
        if parsed is not None:
            qualified[parsed["dissemination_identifier"]] = parsed
    trades = list(qualified.values())
    return {
        "raw_rows": len(payload["tradeList"]),
        "qualified_rows": len(trades),
        "eur_notional": sum(item["eur_notional"] for item in trades),
        "usd_premium": sum(item["usd_premium"] for item in trades),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def normalize(output_root: Path, dates: pd.DatetimeIndex) -> dict[str, Any]:
    raw_root = output_root / "raw"
    records: list[dict[str, Any]] = []
    for date in dates:
        call = parse_daily(
            raw_root / f"{date:%Y%m%d}_CALL.json",
            "CALL",
            date,
        )
        put = parse_daily(
            raw_root / f"{date:%Y%m%d}_PUT.json",
            "PUT",
            date,
        )
        records.append(
            {
                "trade_date": date,
                "available_time_utc": (
                    date + pd.Timedelta(days=1)
                ).tz_localize("UTC"),
                "call_raw_rows": call["raw_rows"],
                "put_raw_rows": put["raw_rows"],
                "call_qualified_trades": call["qualified_rows"],
                "put_qualified_trades": put["qualified_rows"],
                "call_eur_notional": call["eur_notional"],
                "put_eur_notional": put["eur_notional"],
                "call_usd_premium": call["usd_premium"],
                "put_usd_premium": put["usd_premium"],
                "qualified_total_trades": (
                    call["qualified_rows"] + put["qualified_rows"]
                ),
                "qualified_total_eur_notional": (
                    call["eur_notional"] + put["eur_notional"]
                ),
                "qualified_total_usd_premium": (
                    call["usd_premium"] + put["usd_premium"]
                ),
            }
        )
    frame = pd.DataFrame(records).sort_values("trade_date")
    normalized_path = output_root / "DTCC_EURUSD_VANILLA_FLOW.parquet"
    frame.to_parquet(normalized_path, index=False)

    raw_paths = sorted(raw_root.glob("*.json"))
    chain = hashlib.sha256()
    for path in raw_paths:
        chain.update(path.name.encode("ascii"))
        chain.update(bytes.fromhex(sha256_file(path)))
    active = frame[frame["qualified_total_trades"].gt(0)]
    manifest = {
        "campaign": "eurusd-neutral-dtcc-fx-options-v1",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "DTCC Public Price Dissemination CFTC search",
        "source_dashboard": "https://pddata.dtcc.com/ppd/search",
        "source_endpoint": ENDPOINT,
        "queries": {
            "jurisdiction": "CFTC",
            "asset_class": "FOREIGNEXCHANGE",
            "upi_short_names": UPI_SHORT_NAMES,
            "display_type": "w",
        },
        "qualification": {
            "action_type": "NEWT",
            "event_type": "TRAD",
            "package_indicator": "FALSE",
            "underlier": "EUR USD",
            "maximum_report_delay_hours": 24,
            "minimum_tenor_days": 7,
            "maximum_tenor_days": 90,
            "required_premium_currency": "USD",
            "required_directional_notional_currency": "EUR",
            "deduplicate_key": "disseminationIdentifier",
        },
        "credentials_used": False,
        "cost_usd": 0.0,
        "raw_files": len(raw_paths),
        "raw_chain_sha256": chain.hexdigest(),
        "normalized_path": str(normalized_path),
        "normalized_sha256": sha256_file(normalized_path),
        "calendar_rows": len(frame),
        "active_source_sessions": len(active),
        "first_trade_date": frame["trade_date"].min().date().isoformat(),
        "last_trade_date": frame["trade_date"].max().date().isoformat(),
        "qualified_calls": int(frame["call_qualified_trades"].sum()),
        "qualified_puts": int(frame["put_qualified_trades"].sum()),
        "call_eur_notional": float(frame["call_eur_notional"].sum()),
        "put_eur_notional": float(frame["put_eur_notional"].sum()),
        "call_usd_premium": float(frame["call_usd_premium"].sum()),
        "put_usd_premium": float(frame["put_usd_premium"].sum()),
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["manifest_sha256"] = sha256_file(manifest_path)
    return manifest


def acquire(
    output_root: Path,
    start_date: str,
    end_date: str,
    *,
    workers: int,
    force: bool,
    maximum_attempts: int,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range(start_date, end_date, freq="D")
    jobs = [
        (date, option_kind)
        for date in dates
        for option_kind in UPI_SHORT_NAMES
    ]
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                fetch_one,
                date,
                option_kind,
                raw_root,
                force=force,
                maximum_attempts=maximum_attempts,
            ): (date, option_kind)
            for date, option_kind in jobs
        }
        for future in as_completed(futures):
            future.result()
            completed += 1
            if completed % 50 == 0 or completed == len(jobs):
                print(
                    f"Retrieved {completed}/{len(jobs)} DTCC queries",
                    flush=True,
                )
    return normalize(output_root, dates)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--start-date", default="2025-07-29")
    parser.add_argument("--end-date", default="2026-06-30")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--maximum-attempts", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = acquire(
        args.output_root,
        args.start_date,
        args.end_date,
        workers=args.workers,
        force=args.force,
        maximum_attempts=args.maximum_attempts,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
